"""
Service for health check logic.
"""

from datetime import datetime

from fastapi import status

from app.api.modules.v1.models.push_model import ApiResponse, HealthStatus
from app.api.modules.v1.services.fcm_service import fcm_service
from app.api.modules.v1.services.push_service import push_service
from app.api.modules.v1.services.web_push_service import web_push_service
from app.core.cache.redis_client import redis_client
from app.core.config import settings
from app.core.exceptions.custom_exceptions import HealthServiceError
from app.core.queue.consumer import rabbitmq_consumer


class HealthService:
    """
    Service for health check operations.
    """

    @staticmethod
    async def get_health_status():
        """
        Gather health status for all components.
        """
        checks = {}
        failed_checks = 0
        try:
            queue_stats = await rabbitmq_consumer.get_queue_stats()
            if "error" in queue_stats:
                checks["rabbitmq"] = {"status": "down", "error": queue_stats["error"]}
                failed_checks += 1
            else:
                checks["rabbitmq"] = {
                    "status": "up",
                    "queue_length": queue_stats.get("message_count", 0),
                    "consumers": queue_stats.get("consumer_count", 0),
                }
        except Exception as e:
            raise HealthServiceError(f"RabbitMQ health check failed: {str(e)}")
        try:
            redis_health = await redis_client.health_check()
            if redis_health["status"] == "up":
                checks["redis"] = redis_health
            else:
                checks["redis"] = redis_health
                failed_checks += 1
        except Exception as e:
            raise HealthServiceError(f"Redis health check failed: {str(e)}")
        if settings.FCM_ENABLED:
            fcm_circuit = fcm_service.get_circuit_status()
            checks["fcm"] = {
                "status": "up" if fcm_circuit["state"] != "open" else "degraded",
                "circuit_state": fcm_circuit["state"],
                "failure_count": fcm_circuit["failure_count"],
            }
            if fcm_circuit["state"] == "open":
                failed_checks += 0.5
        if settings.WEB_PUSH_ENABLED:
            web_push_circuit = web_push_service.get_circuit_status()
            checks["web_push"] = {
                "status": "up" if web_push_circuit["state"] != "open" else "degraded",
                "circuit_state": web_push_circuit["state"],
                "failure_count": web_push_circuit["failure_count"],
            }
            if web_push_circuit["state"] == "open":
                failed_checks += 0.5
        try:
            metrics = push_service.get_metrics()
            checks["metrics"] = metrics
        except Exception:
            pass
        if failed_checks == 0:
            overall_status = "healthy"
            http_status = status.HTTP_200_OK
        elif failed_checks < 2:
            overall_status = "degraded"
            http_status = status.HTTP_200_OK
        else:
            overall_status = "unhealthy"
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE
        health_data = HealthStatus(
            status=overall_status, version=settings.APP_VERSION, checks=checks
        )
        response = ApiResponse(
            success=(overall_status != "unhealthy"),
            data=health_data,
            message=f"Service is {overall_status}",
        )
        content = response.model_dump()
        if content.get("data") and hasattr(content["data"], "get"):
            if "timestamp" in content["data"] and isinstance(
                content["data"]["timestamp"], datetime
            ):
                content["data"]["timestamp"] = content["data"]["timestamp"].isoformat()
        return http_status, content
