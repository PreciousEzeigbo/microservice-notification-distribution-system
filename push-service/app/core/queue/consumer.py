"""
RabbitMQ Consumer

Reads push notification requests from the push.queue.
Implements:
- Message acknowledgment
- Prefetch limiting (QoS)
- Dead letter queue routing for failed messages
- Graceful shutdown
- Automatic reconnection
"""

import asyncio
import json
import logging
from typing import Optional

import aio_pika
from aio_pika import ExchangeType, Message, connect_robust
from aio_pika.abc import AbstractIncomingMessage

from app.api.modules.v1.models.push_model import ProcessingStatus
from app.api.modules.v1.services.push_service import push_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class RabbitMQConsumer:
    """
    RabbitMQ consumer for push notification queue.
    """

    def __init__(self):
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None
        self.queue: Optional[aio_pika.Queue] = None
        self.is_consuming = False
        self._consumer_tag: Optional[str] = None

    async def connect(self):
        """Establish connection to RabbitMQ with retry."""
        try:
            logger.info(
                f"Connecting to RabbitMQ: {settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}"
            )

            self.connection = await connect_robust(
                settings.rabbitmq_url, heartbeat=60, connection_attempts=5, retry_delay=2
            )

            self.channel = await self.connection.channel()

            await self.channel.set_qos(prefetch_count=settings.RABBITMQ_PREFETCH_COUNT)

            self.exchange = await self.channel.declare_exchange(
                settings.RABBITMQ_EXCHANGE, ExchangeType.DIRECT, durable=True
            )

            self.queue = await self.channel.declare_queue(
                settings.RABBITMQ_PUSH_QUEUE,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": settings.RABBITMQ_EXCHANGE,
                    "x-dead-letter-routing-key": "failed",
                },
            )

            await self.queue.bind(self.exchange, routing_key="push")

            failed_queue = await self.channel.declare_queue(
                settings.RABBITMQ_FAILED_QUEUE, durable=True
            )

            await failed_queue.bind(self.exchange, routing_key="failed")

            logger.info("✓ RabbitMQ connected and configured")

        except Exception as e:
            logger.error(f"✗ RabbitMQ connection failed: {str(e)}")
            raise

    async def disconnect(self):
        """Gracefully disconnect from RabbitMQ."""
        try:
            if self._consumer_tag and self.queue:
                await self.queue.cancel(self._consumer_tag)

            if self.channel and not self.channel.is_closed:
                await self.channel.close()

            if self.connection and not self.connection.is_closed:
                await self.connection.close()

            logger.info("RabbitMQ disconnected")

        except Exception as e:
            logger.error(f"Error during RabbitMQ disconnect: {str(e)}")

    async def start_consuming(self):
        """Start consuming messages from the queue."""
        if not self.queue:
            raise RuntimeError("Not connected to RabbitMQ. Call connect() first.")

        self.is_consuming = True

        logger.info(
            f"Started consuming from '{settings.RABBITMQ_PUSH_QUEUE}' "
            f"(prefetch: {settings.RABBITMQ_PREFETCH_COUNT})"
        )

        # Start consuming with callback
        self._consumer_tag = await self.queue.consume(
            self._process_message,
            no_ack=False,  # Manual acknowledgment
        )

    async def stop_consuming(self):
        """Stop consuming messages."""
        self.is_consuming = False

        if self._consumer_tag and self.queue:
            await self.queue.cancel(self._consumer_tag)
            logger.info("Stopped consuming messages")

    async def _process_message(self, message: AbstractIncomingMessage):
        """
        Process incoming message from queue.

        Message flow:
        1. Parse and validate message
        2. Process notification
        3. ACK on success
        4. NACK with requeue on transient failure
        5. NACK without requeue on permanent failure (goes to DLQ)
        """
        correlation_id = message.correlation_id or "unknown"

        try:
            body = json.loads(message.body.decode())

            if body.get("notification_type") == "push":
                logger.info(
                    f"Processing push message: correlation_id={correlation_id}, "
                    f"request_id={body.get('request_id', 'unknown')}"
                )

                if (
                    "device_tokens" not in body
                    or "platform" not in body
                    or "notification" not in body
                ):
                    from app.api.modules.v1.models.push_model import (
                        NotificationPriority,
                        PushNotificationRequest,
                        PushPlatform,
                        RichNotificationData,
                    )
                    from app.core.clients.device_token_client import device_token_client
                    from app.core.clients.template_client import template_client

                    platform_value = body.get("platform", PushPlatform.FCM.value)
                    try:
                        platform = PushPlatform(platform_value)
                    except ValueError:
                        raise ValueError(f"Unsupported platform: {platform_value}")

                    device_tokens = await device_token_client.get_tokens_for_user(
                        user_id=body["user_id"], platform=platform.value
                    )

                    if not device_tokens:
                        logger.warning(
                            f"No device tokens for user {body['user_id']}. "
                            f"Acknowledging message without processing."
                        )
                        await message.ack()
                        return

                    rendered = await template_client.render_template(
                        template_code=body["template_code"],
                        variables=body.get("variables", {}).__dict__
                        if hasattr(body.get("variables"), "__dict__")
                        else body.get("variables", {}),
                        language=body.get("metadata", {}).get("language"),
                    )

                    notification_data = RichNotificationData(
                        title=rendered["title"],
                        body=rendered["body"],
                        image_url=rendered.get("image_url"),
                        click_action=rendered.get("click_action"),
                        custom_data=body.get("variables", {}).get("meta")
                        if isinstance(body.get("variables"), dict)
                        else {},
                    )
                    push_request = PushNotificationRequest(
                        notification_id=body.get("request_id") or "auto-gen-id",
                        user_id=body["user_id"],
                        device_tokens=device_tokens,
                        platform=platform,
                        notification=notification_data,
                        priority=NotificationPriority.NORMAL,
                        ttl=settings.REDIS_CACHE_TTL,
                        correlation_id=body.get("request_id"),
                    )
                    request = push_request
                else:
                    from app.api.modules.v1.models.push_model import PushNotificationRequest

                    request = PushNotificationRequest(**body)

                response = await push_service.send_notification(request)

                if response.status == ProcessingStatus.SENT:
                    await message.ack()
                    logger.info(f"✓ Message processed successfully: {request.notification_id}")
                elif response.status == ProcessingStatus.FAILED:
                    await message.nack(requeue=False)
                    logger.error(
                        f"✗ Message processing failed permanently: {request.notification_id} (sent to DLQ)"
                    )
                else:
                    await message.nack(requeue=False)
                    logger.warning(
                        f"Message processing resulted in unexpected status: {response.status}"
                    )
            else:
                logger.info(
                    f"Message is not a push notification, skipping. Full body: {json.dumps(body)}"
                )

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {str(e)}")
            await message.nack(requeue=False)

        except ValueError as e:
            logger.error(f"Invalid message format: {str(e)}")
            await message.nack(requeue=False)

        except Exception as e:
            logger.error(f"Error processing message (will retry): {type(e).__name__}: {str(e)}")

            retry_count = self._get_retry_count(message)
            max_retries = settings.MAX_RETRY_ATTEMPTS

            if retry_count >= max_retries:
                logger.error(
                    f"Max retries ({max_retries}) exceeded for message "
                    f"(correlation_id: {correlation_id}). Sending to DLQ."
                )
                await message.nack(requeue=False)
            else:
                logger.info(f"Requeuing message (retry {retry_count + 1}/{max_retries})")
                await message.nack(requeue=True)

    def _get_retry_count(self, message: AbstractIncomingMessage) -> int:
        """Get retry count from message headers."""
        if not message.headers:
            return 0
        return message.headers.get("x-retry-count", 0)

    async def publish_to_failed_queue(
        self, notification_id: str, error: str, original_message: dict
    ):
        """
        Manually publish a message to the failed queue.
        Used when a message needs to be immediately moved to DLQ.
        """
        if not self.exchange:
            raise RuntimeError("Not connected to RabbitMQ")

        failed_message = {
            "notification_id": notification_id,
            "error": error,
            "original_message": original_message,
            "failed_at": str(asyncio.get_event_loop().time()),
        }

        message = Message(
            body=json.dumps(failed_message).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        await self.exchange.publish(message, routing_key="failed")

        logger.info(f"Published to failed queue: {notification_id}")

    async def get_queue_stats(self) -> dict:
        """Get queue statistics."""
        if not self.queue:
            return {"error": "Not connected"}

        try:
            # Passive declare to get queue info without modifying
            info = await self.channel.declare_queue(settings.RABBITMQ_PUSH_QUEUE, passive=True)

            return {
                "queue_name": info.name,
                "message_count": info.declaration_result.message_count,
                "consumer_count": info.declaration_result.consumer_count,
            }
        except Exception as e:
            logger.error(f"Error getting queue stats: {str(e)}")
            return {"error": str(e)}


# Global consumer instance
rabbitmq_consumer = RabbitMQConsumer()
