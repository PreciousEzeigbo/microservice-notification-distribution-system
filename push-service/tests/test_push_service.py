"""Tests for Push Service."""

from unittest.mock import AsyncMock, patch

import pytest

from app.api.modules.v1.models.push_model import (
    NotificationPriority,
    NotificationStatus,
    PushNotificationRequest,
    PushPlatform,
    RichNotificationData,
)
from app.api.modules.v1.services.push_service import PushService


@pytest.fixture
def push_service():
    """Create push service instance."""
    return PushService()


@pytest.mark.asyncio
async def test_send_push_notification_fcm(push_service):
    """Test sending FCM push notification."""
    notification_data = RichNotificationData(
        title="Welcome!", body="Hello John Doe, you have successfully logged in."
    )
    notification = PushNotificationRequest(
        notification_id="test-123",
        user_id="user-456",
        device_tokens=["fcm_token_1", "fcm_token_2"],
        platform=PushPlatform.FCM,
        notification=notification_data,
        priority=NotificationPriority.HIGH,
    )

    with patch(
        "app.api.modules.v1.services.fcm_service.fcm_service.send_notification",
        new=AsyncMock(
            return_value={"sent_count": 2, "failed_count": 0, "invalid_tokens": [], "details": {}}
        ),
    ):
        response = await push_service.send_notification(notification)

        assert response.status == NotificationStatus.SENT


@pytest.mark.asyncio
async def test_send_push_notification_fallback(push_service):
    """Test push service with failures."""
    notification_data = RichNotificationData(title="Test", body="Body")
    notification = PushNotificationRequest(
        notification_id="test-123",
        user_id="user-456",
        device_tokens=["token1"],
        platform=PushPlatform.FCM,
        notification=notification_data,
        priority=NotificationPriority.NORMAL,
    )

    with patch(
        "app.api.modules.v1.services.fcm_service.fcm_service.send_notification",
        new=AsyncMock(return_value={"sent_count": 0, "failed_count": 1}),
    ):
        response = await push_service.send_notification(notification)

        assert response.status == NotificationStatus.FAILED
