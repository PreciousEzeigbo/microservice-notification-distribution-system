"""
Firebase Cloud Messaging (FCM) Service

Sends push notifications to Android and iOS devices via FCM.
Supports:
- Batch sending (up to 500 tokens per request)
- Rich notifications (images, actions, sounds)
- Token validation and cleanup
- Circuit breaker protection
"""

import asyncio
import logging
from typing import Dict, List, Optional

import httpx
from google.auth.transport.requests import Request
from google.oauth2 import service_account

from app.api.modules.v1.models.push_model import PushNotificationRequest, RichNotificationData
from app.api.modules.v1.services.circuit_breaker import CircuitBreaker
from app.core.config import settings
from app.core.exceptions.custom_exceptions import FCMServiceError

logger = logging.getLogger(__name__)


class FCMService:
    """
    Firebase Cloud Messaging service implementation.
    """

    FCM_ENDPOINT = "https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
    BATCH_SIZE = 500  # FCM limit

    def __init__(self):
        self.project_id = settings.FCM_PROJECT_ID
        self.credentials = None
        self.http_client = httpx.AsyncClient(timeout=10.0)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            recovery_timeout=settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
            name="FCM",
        )

        if settings.FCM_ENABLED:
            self._load_credentials()

    def _load_credentials(self):
        """Load Firebase service account credentials."""
        try:
            if not settings.FCM_CREDENTIALS_PATH:
                logger.warning("FCM credentials path not configured")
                return
            self.credentials = service_account.Credentials.from_service_account_file(
                settings.FCM_CREDENTIALS_PATH,
                scopes=["https://www.googleapis.com/auth/firebase.messaging"],
            )
            logger.info("✓ FCM credentials loaded")
        except Exception as e:
            raise FCMServiceError(f"Failed to load FCM credentials: {str(e)}")

    def _get_access_token(self) -> str:
        """Get OAuth2 access token for FCM API."""
        if not self.credentials:
            raise FCMServiceError("FCM credentials not loaded")

        if not self.credentials.valid:
            self.credentials.refresh(Request())

        return self.credentials.token

    def _build_fcm_message(
        self, token: str, notification_data: RichNotificationData, priority: str = "normal"
    ) -> dict:
        """
        Build FCM message payload.

        FCM Message Structure:
        {
            "message": {
                "token": "device_token",
                "notification": {
                    "title": "...",
                    "body": "...",
                    "image": "..."
                },
                "data": {
                    "click_action": "...",
                    "custom_key": "custom_value"
                },
                "android": {...},
                "apns": {...}
            }
        }
        """
        message = {
            "message": {
                "token": token,
                "notification": {"title": notification_data.title, "body": notification_data.body},
            }
        }

        if notification_data.image_url:
            message["message"]["notification"]["image"] = str(notification_data.image_url)

        data_payload = {}

        if notification_data.click_action:
            data_payload["click_action"] = str(notification_data.click_action)

        if notification_data.custom_data:
            # FCM data payload only accepts string values - stringify all custom_data
            stringified_custom_data = {k: str(v) for k, v in notification_data.custom_data.items()}
            data_payload.update(stringified_custom_data)

        if data_payload:
            message["message"]["data"] = data_payload

        message["message"]["android"] = {
            "priority": priority,
            "notification": {
                "sound": notification_data.sound or "default",
                "click_action": "FLUTTER_NOTIFICATION_CLICK",
            },
        }

        if notification_data.icon_url:
            message["message"]["android"]["notification"]["icon"] = str(notification_data.icon_url)

        if notification_data.tag:
            message["message"]["android"]["notification"]["tag"] = notification_data.tag

        message["message"]["apns"] = {
            "headers": {"apns-priority": "10" if priority == "high" else "5"},
            "payload": {
                "aps": {
                    "alert": {"title": notification_data.title, "body": notification_data.body},
                    "sound": notification_data.sound or "default",
                }
            },
        }

        if notification_data.badge_count is not None:
            message["message"]["apns"]["payload"]["aps"]["badge"] = notification_data.badge_count

        return message

    async def _send_single(
        self,
        token: str,
        notification_data: RichNotificationData,
        priority: str = "normal",
        validate_only: bool = False,
    ) -> tuple[bool, Optional[str]]:
        """
        Send notification to a single device token.

        Args:
            token: Device FCM token
            notification_data: Rich notification content
            priority: Message priority (normal/high)
            validate_only: If True, performs dry-run validation without sending

        Returns:
            (success, error_message)
        """
        try:
            access_token = self._get_access_token()
            endpoint = self.FCM_ENDPOINT.format(project_id=self.project_id)

            message = self._build_fcm_message(token, notification_data, priority)

            # Add validate_only flag for dry-run validation
            if validate_only:
                message["validate_only"] = True

            async def _send():
                response = await self.http_client.post(
                    endpoint,
                    json=message,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
                return response.json()

            await self.circuit_breaker.call(_send)
            logger.debug(f"FCM send success: {token[:20]}...")
            return True, None

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}"
            if e.response.status_code == 404:
                error_msg = "Invalid token (not registered)"
            elif e.response.status_code == 400:
                error_msg = "Invalid request"
            elif e.response.status_code >= 500:
                error_msg = "FCM server error"
            logger.warning(f"FCM send failed: {token[:20]}... - {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error(f"FCM send error: {token[:20]}... - {error_msg}")
            return False, error_msg

    async def _send_batch(
        self, tokens: List[str], notification_data: RichNotificationData, priority: str
    ) -> dict:
        """Send a batch of notifications concurrently."""
        sent_count = 0
        failed_count = 0
        invalid_tokens = []
        errors = []

        tasks = [self._send_single(token, notification_data, priority) for token in tokens]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for token, result in zip(tokens, results):
            if isinstance(result, tuple) and result[0]:
                sent_count += 1
            else:
                failed_count += 1
                # Extract error message from tuple result or convert other types
                error_payload = (
                    result[1] if isinstance(result, (tuple, list)) and len(result) > 1 else result
                )
                error_message = str(error_payload)
                if "Invalid token" in error_message:
                    invalid_tokens.append(token)
                errors.append({"token": token, "error": error_message})

        return {
            "sent_count": sent_count,
            "failed_count": failed_count,
            "invalid_tokens": invalid_tokens,
            "details": {"errors": errors if errors else None},
        }

    async def send_notification(self, request: PushNotificationRequest) -> Dict:
        """
        Send push notification to multiple device tokens.

        Returns:
            {
                "sent_count": int,
                "failed_count": int,
                "invalid_tokens": List[str],
                "details": Dict
            }
        """
        if not settings.FCM_ENABLED:
            return {
                "sent_count": 0,
                "failed_count": len(request.device_tokens),
                "invalid_tokens": [],
                "details": {"error": "FCM is disabled"},
            }

        sent_count = 0
        failed_count = 0
        invalid_tokens = []
        errors = []

        for i in range(0, len(request.device_tokens), self.BATCH_SIZE):
            batch_tokens = request.device_tokens[i : i + self.BATCH_SIZE]
            batch_result = await self._send_batch(
                batch_tokens, request.notification, request.priority.value
            )
            sent_count += batch_result["sent_count"]
            failed_count += batch_result["failed_count"]
            invalid_tokens.extend(batch_result["invalid_tokens"])
            if batch_result["details"]["errors"]:
                errors.extend(batch_result["details"]["errors"])

        logger.info(
            f"FCM batch complete: {sent_count} sent, {failed_count} failed "
            f"(notification_id: {request.notification_id})"
        )

        return {
            "sent_count": sent_count,
            "failed_count": failed_count,
            "invalid_tokens": invalid_tokens,
            "details": {"errors": errors if errors else None},
        }

    async def validate_token(self, token: str) -> bool:
        """
        Validate if a device token is still valid.

        This is a dry-run send to check token validity without sending a real notification.
        """
        try:
            # Use a minimal test notification with validate_only flag
            test_notification = RichNotificationData(title="Test", body="Token validation")

            success, _ = await self._send_single(
                token, test_notification, priority="low", validate_only=True
            )

            return success

        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return False

    def get_circuit_status(self) -> dict:
        """Get circuit breaker status."""
        return self.circuit_breaker.get_status()

    async def close(self):
        """Close HTTP client during shutdown."""
        await self.http_client.aclose()
        logger.info("FCM service HTTP client closed")


# Global FCM service instance
fcm_service = FCMService()
