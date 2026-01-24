import logging
from datetime import datetime
from enum import Enum
from typing import Optional

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.api.modules.v1.models.push_model import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/push",
    tags=["Push Status"],
)


class DeliveryStatus(str, Enum):
    """Notification delivery status as per task specification."""

    DELIVERED = "delivered"
    PENDING = "pending"
    FAILED = "failed"


class PushStatusReport(BaseModel):
    """Status report format as per task: POST /api/v1/{notification_preference}/status/"""

    notification_id: str = Field(..., description="Notification UUID")
    status: DeliveryStatus = Field(..., description="Delivery status")
    timestamp: Optional[datetime] = Field(None, description="Status timestamp (UTC ISO format)")
    error: Optional[str] = Field(None, description="Error message if failed, else null")


@router.post(
    "/status",
    status_code=status.HTTP_200_OK,
    summary="Report Push Notification Status",
    description="Endpoint for reporting push notification delivery status. "
    "This would typically be called by the API Gateway or stored for status tracking.",
)
async def report_push_status(payload: PushStatusReport):
    """
    Report push notification delivery status.

    As per task specification: POST /api/v1/{notification_preference}/status/

    In a production system:
    1. Store status in database for tracking
    2. Forward to API Gateway for client queries
    3. Update delivery metrics
    4. Trigger webhooks if configured
    """
    logger.info(
        f"Push status: notification_id={payload.notification_id}, "
        f"status={payload.status}, error={payload.error}"
    )

    # TODO: Store status in database or forward to API Gateway
    # TODO: Update metrics/monitoring

    return ApiResponse(
        success=True,
        message="Status received and recorded",
        data={"notification_id": payload.notification_id, "status": payload.status},
    )
