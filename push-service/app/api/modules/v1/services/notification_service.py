import logging
import uuid
from datetime import datetime

from app.core.queue.producer import rabbitmq_producer

from app.api.modules.v1.models.notification_model import NotificationRequest
from app.api.modules.v1.models.push_model import (
    NotificationPriority,
    PushNotificationRequest,
    PushPlatform,
    RichNotificationData,
)
from app.core.clients.device_token_client import device_token_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for handling notification requests and transforming them for push delivery.
    """

    async def send(self, payload: NotificationRequest):
        """
        Process a notification request and publish to the push queue.
        """
        logger.info(f"Processing notification: {payload}")

        # Determine platform
        if payload.notification_type == "push":
            platform = PushPlatform.FCM
            platform_filter = "fcm"
        else:
            platform = PushPlatform.WEB_PUSH
            platform_filter = "web_push"

        # Fetch device tokens from device service (or dummy tokens if not configured)
        device_tokens = await device_token_client.get_tokens_for_user(
            user_id=payload.user_id, platform=platform_filter
        )

        if not device_tokens:
            logger.warning(f"No device tokens found for user {payload.user_id}")
            return {
                "request_id": payload.request_id,
                "status": "no_devices",
                "message": "No device tokens found",
            }

        # TODO: Fetch actual notification content from template service
        # This is a placeholder - should render template with variables
        notification_data = RichNotificationData(
            title=f"Notification for {payload.user_id}",
            body=f"Template: {payload.template_code}",
            custom_data=payload.variables.meta or {},
        )

        request_id = payload.request_id or str(uuid.uuid4())

        push_request = PushNotificationRequest(
            notification_id=request_id,
            user_id=payload.user_id,
            device_tokens=device_tokens,
            platform=platform,
            notification=notification_data,
            priority=NotificationPriority.NORMAL,
            ttl=settings.REDIS_CACHE_TTL,  # Use configurable TTL instead of hardcoded value
            correlation_id=request_id,
            created_at=datetime.utcnow(),
        )

        message_body = push_request.model_dump(mode="json")

        await rabbitmq_producer.publish_message(
            routing_key=settings.RABBITMQ_PUSH_QUEUE,
            message_body=message_body,
            correlation_id=push_request.correlation_id,
        )

        logger.info(f"Published notification to RabbitMQ: {request_id}")

        return {"request_id": request_id, "status": "queued"}
