"""
Web Push Service with VAPID

Sends push notifications to web browsers (PWA).
Uses VAPID (Voluntary Application Server Identification) for authentication.

Supported browsers:
- Chrome/Edge (via FCM)
- Firefox (Mozilla Push Service)
- Safari (Apple Push Service)
"""

import asyncio
import json
import logging
from typing import Dict, Optional

from pywebpush import WebPushException, webpush

from app.api.modules.v1.models.push_model import PushNotificationRequest, RichNotificationData
from app.api.modules.v1.services.circuit_breaker import CircuitBreaker
from app.core.config import settings

logger = logging.getLogger(__name__)


class WebPushService:
    """
    Web Push notification service using VAPID protocol.
    """

    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            recovery_timeout=settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
            name="WebPush",
        )

        if settings.WEB_PUSH_ENABLED:
            self._validate_config()

    def _validate_config(self):
        """Validate Web Push configuration."""
        if not settings.VAPID_PRIVATE_KEY or not settings.VAPID_PUBLIC_KEY:
            logger.warning("Web Push VAPID keys not configured")
        else:
            logger.info("✓ Web Push VAPID configured")

    def _build_web_push_payload(self, notification_data: RichNotificationData) -> dict:
        """
        Build Web Push notification payload.

        Web Push Notification Structure:
        {
            "notification": {
                "title": "...",
                "body": "...",
                "icon": "...",
                "image": "...",
                "badge": "...",
                "tag": "...",
                "data": {
                    "url": "...",
                    "custom": "..."
                },
                "actions": [...]
            }
        }
        """
        payload = {
            "notification": {
                "title": notification_data.title,
                "body": notification_data.body,
                "icon": str(notification_data.icon_url)
                if notification_data.icon_url
                else "/icon.png",
                "badge": "/badge.png",
                "requireInteraction": False,
                "silent": False,
            }
        }

        # Add image
        if notification_data.image_url:
            payload["notification"]["image"] = str(notification_data.image_url)

        # Add tag for grouping
        if notification_data.tag:
            payload["notification"]["tag"] = notification_data.tag

        # Add click action and custom data
        data = {}
        if notification_data.click_action:
            data["url"] = str(notification_data.click_action)

        if notification_data.custom_data:
            data.update(notification_data.custom_data)

        if data:
            payload["notification"]["data"] = data

        return payload

    def _parse_subscription(self, token: str) -> Optional[dict]:
        """
        Parse Web Push subscription from token.

        Token format should be JSON string:
        {
            "endpoint": "https://...",
            "keys": {
                "p256dh": "...",
                "auth": "..."
            }
        }
        """
        try:
            subscription = json.loads(token)

            # Validate required fields
            if "endpoint" not in subscription:
                logger.error("Invalid subscription: missing endpoint")
                return None

            if "keys" not in subscription:
                logger.error("Invalid subscription: missing keys")
                return None

            keys = subscription["keys"]
            if "p256dh" not in keys or "auth" not in keys:
                logger.error("Invalid subscription: missing p256dh or auth keys")
                return None

            return subscription

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse subscription token: {str(e)}")
            return None

    async def _send_single(
        self, subscription: dict, notification_data: RichNotificationData, ttl: int = 86400
    ) -> tuple[bool, Optional[str]]:
        """
        Send Web Push notification to a single subscription.

        Args:
            subscription: Web Push subscription object
            notification_data: Notification content
            ttl: Time to live in seconds

        Returns:
            (success, error_message)
        """
        try:
            payload = self._build_web_push_payload(notification_data)
            payload_json = json.dumps(payload)

            # Send via circuit breaker
            async def _send():
                return await asyncio.to_thread(
                    webpush,
                    subscription_info=subscription,
                    data=payload_json,
                    vapid_private_key=settings.VAPID_PRIVATE_KEY,
                    vapid_claims={"sub": settings.VAPID_SUBJECT},
                    ttl=ttl,
                    timeout=10,
                )

            await self.circuit_breaker.call(_send)
            logger.debug(f"Web Push sent: {subscription['endpoint'][:50]}...")
            return True, None

        except WebPushException as e:
            error_msg = str(e)
            if e.response:
                status_code = e.response.status_code
                if status_code == 410:
                    error_msg = "Subscription expired or unsubscribed"
                elif status_code == 404:
                    error_msg = "Subscription not found"
                elif status_code == 401:
                    error_msg = "Invalid VAPID credentials"
                elif status_code >= 500:
                    error_msg = "Push service server error"
            logger.warning(f"Web Push failed: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error(f"Web Push error: {error_msg}")
            return False, error_msg

    async def send_notification(self, request: PushNotificationRequest) -> Dict:
        """
        Send Web Push notification to multiple subscriptions.

        Returns:
            {
                "sent_count": int,
                "failed_count": int,
                "invalid_tokens": List[str],
                "details": Dict
            }
        """
        if not settings.WEB_PUSH_ENABLED:
            return {
                "sent_count": 0,
                "failed_count": len(request.device_tokens),
                "invalid_tokens": [],
                "details": {"error": "Web Push is disabled"},
            }

        sent_count = 0
        failed_count = 0
        invalid_tokens = []
        errors = []

        subscriptions = [self._parse_subscription(token) for token in request.device_tokens]
        valid_subscriptions = [s for s in subscriptions if s]
        invalid_subscriptions = [
            token for token, s in zip(request.device_tokens, subscriptions) if not s
        ]

        failed_count += len(invalid_subscriptions)
        invalid_tokens.extend(invalid_subscriptions)
        errors.extend(
            [
                {"token": token, "error": "Invalid subscription format"}
                for token in invalid_subscriptions
            ]
        )

        tasks = [
            self._send_single(sub, request.notification, request.ttl or 86400)
            for sub in valid_subscriptions
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for sub, result in zip(valid_subscriptions, results):
            if isinstance(result, tuple) and result[0]:
                sent_count += 1
            else:
                failed_count += 1
                error_message = str(result)
                if "expired" in error_message.lower() or "not found" in error_message.lower():
                    invalid_tokens.append(json.dumps(sub))
                errors.append({"endpoint": sub["endpoint"], "error": error_message})

        logger.info(
            f"Web Push batch complete: {sent_count} sent, {failed_count} failed "
            f"(notification_id: {request.notification_id})"
        )

        return {
            "sent_count": sent_count,
            "failed_count": failed_count,
            "invalid_tokens": invalid_tokens,
            "details": {"errors": errors if errors else None},
        }

    def get_circuit_status(self) -> dict:
        """Get circuit breaker status."""
        return self.circuit_breaker.get_status()


# Global Web Push service instance
web_push_service = WebPushService()
