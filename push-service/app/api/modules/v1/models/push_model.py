"""
Pydantic Models for Request/Response Validation
These models ensure type safety and automatic validation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field, HttpUrl


# Enums
class PushPlatform(str, Enum):
    """Supported push notification platforms."""

    FCM = "fcm"
    APNS = "apns"
    WEB_PUSH = "web_push"


class NotificationPriority(str, Enum):
    """Notification delivery priority."""

    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class ProcessingStatus(str, Enum):
    """Notification processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"
    EXPIRED = "expired"


class PaginationMeta(BaseModel):
    """Standard pagination metadata."""

    total: int = Field(ge=0, description="Total number of items")
    limit: int = Field(ge=1, le=100, description="Items per page")
    page: int = Field(ge=1, description="Current page number")
    total_pages: int = Field(ge=0, description="Total number of pages")
    has_next: bool = Field(description="Has next page")
    has_previous: bool = Field(description="Has previous page")


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    success: bool = Field(description="Operation success status")
    data: Optional[T] = Field(default=None, description="Response data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    message: str = Field(description="Human-readable message")
    meta: Optional[PaginationMeta] = Field(default=None, description="Pagination metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"notification_id": "123"},
                "message": "Notification sent successfully",
                "error": None,
                "meta": None,
            }
        }


class RichNotificationData(BaseModel):
    """Rich notification content with media and actions."""

    title: str = Field(..., min_length=1, max_length=100, description="Notification title")
    body: str = Field(..., min_length=1, max_length=500, description="Notification body text")
    image_url: Optional[HttpUrl] = Field(
        default=None, description="Image URL for rich notification"
    )
    icon_url: Optional[HttpUrl] = Field(default=None, description="Icon URL")
    click_action: Optional[HttpUrl] = Field(default=None, description="URL to open on click")
    badge_count: Optional[int] = Field(default=None, ge=0, description="Badge count (iOS/Android)")
    sound: Optional[str] = Field(default="default", description="Notification sound")
    tag: Optional[str] = Field(default=None, description="Notification tag for grouping")
    custom_data: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Custom key-value data"
    )


class DeviceToken(BaseModel):
    """Device registration token."""

    token: str = Field(..., min_length=1, description="Device push token")
    platform: PushPlatform = Field(..., description="Platform type")
    user_id: str = Field(..., description="User identifier")
    is_active: bool = Field(default=True, description="Token validity status")


class PushNotificationRequest(BaseModel):
    """
    Push notification request from queue.
    This is the message format expected from RabbitMQ.
    """

    notification_id: str = Field(..., description="Unique notification ID (idempotency)")
    user_id: str = Field(..., description="Target user ID")
    device_tokens: List[str] = Field(..., min_items=1, description="List of device tokens")
    platform: PushPlatform = Field(..., description="Target platform")
    notification: RichNotificationData = Field(..., description="Notification content")
    priority: NotificationPriority = Field(default=NotificationPriority.NORMAL)
    ttl: Optional[int] = Field(default=86400, ge=0, description="Time to live in seconds")
    correlation_id: Optional[str] = Field(
        default=None, description="Request correlation ID for tracking"
    )
    web_push_subscriptions: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Web push subscription objects for browser notifications"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "notification_id": "notif_123456",
                "user_id": "user_789",
                "device_tokens": ["token_abc123", "token_def456"],
                "platform": "fcm",
                "notification": {
                    "title": "New Message",
                    "body": "You have a new message from John",
                    "image_url": "https://example.com/image.jpg",
                    "click_action": "https://example.com/chat/123",
                },
                "priority": "high",
                "ttl": 86400,
            }
        }


class PushNotificationResponse(BaseModel):
    """Response after sending push notification."""

    notification_id: str
    status: ProcessingStatus
    sent_count: int = Field(ge=0, description="Number of successfully sent notifications")
    failed_count: int = Field(ge=0, description="Number of failed sends")
    invalid_tokens: List[str] = Field(default_factory=list, description="Invalid device tokens")
    details: Optional[Dict[str, Any]] = None
    processed_at: datetime = Field(default_factory=datetime.utcnow)


class HealthStatus(BaseModel):
    """Service health status."""

    status: str = Field(..., description="Overall status: healthy, degraded, unhealthy")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: Dict[str, Any] = Field(default_factory=dict, description="Individual component checks")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2025-01-07T12:00:00Z",
                "checks": {
                    "rabbitmq": {"status": "up", "latency_ms": 5},
                    "redis": {"status": "up", "latency_ms": 2},
                    "fcm": {"status": "up", "circuit_state": "closed"},
                },
            }
        }


class ServiceMetrics(BaseModel):
    """Service performance metrics."""

    messages_processed: int = 0
    messages_sent: int = 0
    messages_failed: int = 0
    avg_processing_time_ms: float = 0.0
    queue_length: int = 0
    circuit_breaker_state: str = "closed"
    uptime_seconds: float = 0.0
