import logging
import time
from typing import Dict, List

from app.api.modules.v1.models.push_model import (
    ProcessingStatus,
    PushNotificationRequest,
    PushNotificationResponse,
    PushPlatform,
)
from app.api.modules.v1.services.fcm_service import fcm_service
from app.api.modules.v1.services.web_push_service import web_push_service
from app.core.cache.redis_client import redis_client
from app.core.config import settings
from app.core.exceptions.custom_exceptions import PushServiceError
from app.utils.retry import create_retry_handler

logger = logging.getLogger(__name__)


class PushService:
    """
    Main push notification service.
    Routes notifications to appropriate platform services.
    """

    def __init__(self):
        self.retry_handler = create_retry_handler(
            max_attempts=settings.MAX_RETRY_ATTEMPTS,
            initial_delay=settings.RETRY_INITIAL_DELAY,
            max_delay=settings.RETRY_MAX_DELAY,
        )

        self.metrics = {
            "total_processed": 0,
            "total_sent": 0,
            "total_failed": 0,
            "start_time": time.time(),
        }

    async def send_notification(self, request: PushNotificationRequest) -> PushNotificationResponse:
        """
        Send push notification with all safety checks.

        Process:
        1. Check idempotency (prevent duplicates)
        2. Check rate limit
        3. Filter invalid tokens (cached)
        4. Route to appropriate platform service
        5. Handle failures and retries
        6. Return response
        """
        start_time = time.time()

        try:
            if await self._check_duplicate(request.notification_id):
                logger.info(f"Duplicate notification skipped: {request.notification_id}")
                return PushNotificationResponse(
                    notification_id=request.notification_id,
                    status=ProcessingStatus.SENT,
                    sent_count=0,
                    failed_count=0,
                    details={"message": "Duplicate request (already processed)"},
                )

            if settings.RATE_LIMIT_ENABLED:
                await self._check_rate_limit(request.user_id)

            valid_tokens = await self._filter_valid_tokens(request.device_tokens)

            if not valid_tokens:
                logger.warning(f"No valid tokens for notification {request.notification_id}")
                return PushNotificationResponse(
                    notification_id=request.notification_id,
                    status=ProcessingStatus.FAILED,
                    sent_count=0,
                    failed_count=len(request.device_tokens),
                    invalid_tokens=request.device_tokens,
                    details={"error": "All tokens are invalid"},
                )

            request.device_tokens = valid_tokens

            result = await self._route_to_platform(request)

            if result["invalid_tokens"]:
                await self._cache_invalid_tokens(result["invalid_tokens"])

            self._update_metrics(result["sent_count"], result["failed_count"])

            status = self._determine_status(result["sent_count"], result["failed_count"])

            processing_time = (time.time() - start_time) * 1000  # ms

            logger.info(
                f"Notification {request.notification_id} processed: "
                f"status={status.value}, sent={result['sent_count']}, "
                f"failed={result['failed_count']}, time={processing_time:.2f}ms"
            )

            return PushNotificationResponse(
                notification_id=request.notification_id,
                status=status,
                sent_count=result["sent_count"],
                failed_count=result["failed_count"],
                invalid_tokens=result["invalid_tokens"],
                details={
                    "processing_time_ms": round(processing_time, 2),
                    "platform": request.platform.value,
                    **result["details"],
                },
            )

        except Exception as e:
            logger.error(
                f"Error processing notification {request.notification_id}: "
                f"{type(e).__name__}: {str(e)}"
            )

            return PushNotificationResponse(
                notification_id=request.notification_id,
                status=ProcessingStatus.FAILED,
                sent_count=0,
                failed_count=len(request.device_tokens),
                details={"error": str(e)},
            )

    async def _check_duplicate(self, notification_id: str) -> bool:
        """Check if notification was already processed (idempotency)."""
        try:
            return await redis_client.check_and_set_idempotency(notification_id)
        except Exception as e:
            raise PushServiceError(f"Idempotency check failed: {str(e)}")

    async def _check_rate_limit(self, user_id: str):
        """Check and enforce rate limiting."""
        try:
            is_allowed, count = await redis_client.check_rate_limit(
                user_id, limit=settings.RATE_LIMIT_PER_MINUTE, window=60
            )
            if not is_allowed:
                raise PushServiceError(
                    f"Rate limit exceeded for user {user_id}: "
                    f"{count}/{settings.RATE_LIMIT_PER_MINUTE} per minute"
                )
        except Exception as e:
            raise PushServiceError(f"Rate limit check failed: {str(e)}")

    async def _filter_valid_tokens(self, tokens: List[str]) -> List[str]:
        """Filter out tokens that are cached as invalid."""
        try:
            invalid_mask = await redis_client.are_tokens_invalid(tokens)
            valid_tokens = [
                token for token, is_invalid in zip(tokens, invalid_mask) if not is_invalid
            ]
            return valid_tokens
        except Exception as e:
            raise PushServiceError(f"Token validation check failed: {str(e)}")

    async def _cache_invalid_tokens(self, tokens: List[str]):
        """Cache invalid tokens to avoid future send attempts."""
        try:
            await redis_client.cache_invalid_tokens(tokens)
        except Exception as e:
            raise PushServiceError(f"Failed to cache invalid token: {str(e)}")

    async def _route_to_platform(self, request: PushNotificationRequest) -> Dict:
        """
        Route notification to appropriate platform service.
        Uses retry handler for transient failures.
        """

        async def _send():
            if request.platform == PushPlatform.FCM:
                return await fcm_service.send_notification(request)
            elif request.platform == PushPlatform.WEB_PUSH:
                return await web_push_service.send_notification(request)
            else:
                raise PushServiceError(f"Unsupported platform: {request.platform}")

        # Execute with retry
        return await self.retry_handler.execute(
            _send, context=f"notification_id={request.notification_id}"
        )

    def _determine_status(self, sent_count: int, failed_count: int) -> ProcessingStatus:
        """Determine overall notification status."""
        if sent_count > 0 and failed_count == 0:
            return ProcessingStatus.SENT
        elif sent_count == 0:
            return ProcessingStatus.FAILED
        else:
            return ProcessingStatus.SENT

    def _update_metrics(self, sent_count: int, failed_count: int):
        """Update service metrics."""
        self.metrics["total_processed"] += 1
        self.metrics["total_sent"] += sent_count
        self.metrics["total_failed"] += failed_count

    def get_metrics(self) -> dict:
        """Get current service metrics."""
        uptime = time.time() - self.metrics["start_time"]

        return {
            "total_processed": self.metrics["total_processed"],
            "total_sent": self.metrics["total_sent"],
            "total_failed": self.metrics["total_failed"],
            "success_rate": (self.metrics["total_sent"] / max(1, self.metrics["total_processed"]))
            * 100,
            "uptime_seconds": round(uptime, 2),
            "fcm_circuit": fcm_service.get_circuit_status(),
            "web_push_circuit": web_push_service.get_circuit_status(),
        }


push_service = PushService()
