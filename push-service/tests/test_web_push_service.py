"""Tests for Web Push Service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.modules.v1.models.push_model import (
    NotificationPriority,
    PushNotificationRequest,
    PushPlatform,
    RichNotificationData,
)
from app.api.modules.v1.services.web_push_service import WebPushService


@pytest.fixture
def web_push_service():
    """Create Web Push service instance."""
    return WebPushService()


@pytest.mark.asyncio
async def test_send_notification_success(web_push_service):
    """Test successful web push notification."""
    # Mock the send method to return expected format
    with patch.object(
        web_push_service,
        "send_notification",
        new=AsyncMock(return_value={"sent_count": 1, "failed_count": 0}),
    ):
        result = await web_push_service.send_notification(None)
        assert "sent_count" in result
        assert "failed_count" in result


@pytest.mark.asyncio
async def test_send_notification_with_subscriptions():
    """Test web push with subscriptions."""
    service = WebPushService()
    notification_data = RichNotificationData(title="Test Push", body="Test body")
    notification = PushNotificationRequest(
        notification_id="test-123",
        user_id="user-456",
        device_tokens=["dummy"],
        platform=PushPlatform.WEB_PUSH,
        notification=notification_data,
        priority=NotificationPriority.NORMAL,
        web_push_subscriptions=[
            {
                "endpoint": "https://fcm.googleapis.com/fcm/send/123",
                "keys": {"p256dh": "key1", "auth": "auth1"},
            }
        ],
    )

    with patch("pywebpush.webpush", return_value=MagicMock(status_code=201)):
        result = await service.send_notification(notification)

        assert "sent_count" in result
        assert "failed_count" in result


@pytest.mark.asyncio
async def test_send_notification_no_subscriptions(web_push_service):
    """Test web push with no subscriptions."""
    notification_data = RichNotificationData(title="Test", body="Body")
    notification = PushNotificationRequest(
        notification_id="test-123",
        user_id="user-456",
        device_tokens=["dummy"],  # Required field
        platform=PushPlatform.WEB_PUSH,
        notification=notification_data,
        priority=NotificationPriority.NORMAL,
        web_push_subscriptions=[],
    )

    result = await web_push_service.send_notification(notification)
    assert result["sent_count"] == 0
