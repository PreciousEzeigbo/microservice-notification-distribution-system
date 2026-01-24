"""Tests for FCM Service."""

from unittest.mock import AsyncMock, patch

import pytest

from app.api.modules.v1.models.push_model import (
    NotificationPriority,
    PushNotificationRequest,
    PushPlatform,
    RichNotificationData,
)
from app.api.modules.v1.services.fcm_service import FCMService


@pytest.fixture
def fcm_service():
    """Create FCM service instance."""
    with patch("firebase_admin.initialize_app"):
        service = FCMService()
        return service


@pytest.mark.asyncio
async def test_send_notification_success(fcm_service):
    """Test successful FCM notification sending."""
    notification_data = RichNotificationData(title="Test Notification", body="Test body")
    notification = PushNotificationRequest(
        notification_id="test-123",
        user_id="user-456",
        device_tokens=["token1", "token2"],
        platform=PushPlatform.FCM,
        notification=notification_data,
        priority=NotificationPriority.HIGH,
    )

    with patch.object(
        fcm_service,
        "_send_batch",
        new=AsyncMock(
            return_value={
                "sent_count": 2,
                "failed_count": 0,
                "invalid_tokens": [],
                "details": {"errors": []},
            }
        ),
    ):
        result = await fcm_service.send_notification(notification)

        assert "sent_count" in result or "sent" in result
        assert "failed_count" in result or "failed" in result


@pytest.mark.asyncio
async def test_send_notification_fcm_disabled(fcm_service):
    """Test FCM when disabled."""
    notification_data = RichNotificationData(title="Test", body="Body")
    notification = PushNotificationRequest(
        notification_id="test-123",
        user_id="user-456",
        device_tokens=["token1"],
        platform=PushPlatform.FCM,
        notification=notification_data,
        priority=NotificationPriority.NORMAL,
    )

    with patch("app.core.config.settings.FCM_ENABLED", False):
        result = await fcm_service.send_notification(notification)
        assert result["sent_count"] == 0
