import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.api.modules.v1.services.health_service import HealthService

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)

logger = logging.getLogger(__name__)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check service health and component status. Returns 200 if healthy, 503 if unhealthy.",
)
async def health_check():
    """
    Comprehensive health check endpoint.
    Returns 200 if healthy, 503 if unhealthy.

    Returns:
        JSONResponse: Success or failure health status and details.
    """
    logger.info("Performing health check.")
    http_status, content = await HealthService.get_health_status()
    logger.info(f"Health check result: status={http_status}")
    return JSONResponse(status_code=http_status, content=content)
