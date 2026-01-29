import uuid
import logging
from datetime import datetime
import httpx

from rest_framework.views import APIView
from rest_framework.response import Response
from asgiref.sync import async_to_sync
from django.db import connection
from django.conf import settings

from core.proxy import proxy_request
from core.serializers import NotificationRequestSerializer
from core.redis_client import redis_client
from observability.models import NotificationAuditLog

logger = logging.getLogger(__name__)


class UserProxy(APIView):
    """
    Gateway reverse proxy for User Service requests.
    """

    def get(self, request, *args, **kwargs):
        return self.handle(request)

    def post(self, request, *args, **kwargs):
        return self.handle(request)

    def put(self, request, *args, **kwargs):
        return self.handle(request)

    def patch(self, request, *args, **kwargs):
        return self.handle(request)

    def delete(self, request, *args, **kwargs):
        return self.handle(request)

    def handle(self, request):
        response = async_to_sync(proxy_request)(request, "USER")

        if not response:
            return Response(
                {"success": False, "message": "User Service unavailable"},
                status=503
            )

        return Response(response.json(), status=response.status_code)


class TemplateProxy(APIView):
    """
    Gateway reverse proxy for Template Service requests.
    """

    def get(self, request, *args, **kwargs):
        return self.handle(request)

    def post(self, request, *args, **kwargs):
        return self.handle(request)

    def put(self, request, *args, **kwargs):
        return self.handle(request)

    def patch(self, request, *args, **kwargs):
        return self.handle(request)

    def delete(self, request, *args, **kwargs):
        return self.handle(request)

    def handle(self, request):
        response = async_to_sync(proxy_request)(request, "TEMPLATE")

        if not response:
            return Response(
                {"success": False, "message": "Template Service unavailable"},
                status=503
            )

        return Response(response.json(), status=response.status_code)


class NotificationGateway(APIView):
    """
    Gateway entry point for queuing notifications.
    Validates payload, enriches metadata, forwards request,
    and stores audit logs even if downstream fails.
    """

    def post(self, request):
        serializer = NotificationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        body = serializer.validated_data

        correlation_id = getattr(request, "correlation_id", str(uuid.uuid4()))
        user_id = request.user.id if request.user.is_authenticated else None

        message = {
            "message_id": str(uuid.uuid4()),
            "request_id": body["request_id"],
            "notification_type": body["notification_type"],
            "user_id": user_id,
            "template_code": body["template_code"],
            "variables": body.get("variables", {}),
            "priority": body.get("priority"),
            "metadata": body.get("metadata"),
            "created_at": datetime.utcnow().isoformat(),
            "correlation_id": correlation_id
        }

        response = async_to_sync(proxy_request)(
            request,
            "NOTIFICATION",
            override_body=message
        )

        status_value = "pending" if response else "failed"

        # Always log audit (even if downstream fails)
        try:
            NotificationAuditLog.objects.create(
                notification_id=message["message_id"],
                request_id=message["request_id"],
                user_id=user_id,
                notification_type=message["notification_type"],
                template_code=message["template_code"],
                status=status_value,
                correlation_id=correlation_id
            )
        except Exception as e:
            logger.error(f"Audit log failed: {e}")

        if not response:
            return Response({
                "success": False,
                "message": "Notification service unavailable",
                "error": "SERVICE_DOWN"
            }, status=503)

        return Response({
            "success": True,
            "data": message,
            "message": "Notification queued"
        }, status=202)


class HealthCheck(APIView):
    """
    Aggregated health endpoint for gateway dependencies.
    Always returns HTTP 200 while reporting degraded services.
    """

    def get(self, request):
        services = {
            "gateway": "up",
            "database": self.check_database(),
            "redis": self.check_redis(),
            "user_service": self.check_service("USER"),
            "template_service": self.check_service("TEMPLATE"),
            "notification_service": self.check_service("NOTIFICATION"),
        }

        overall_status = "healthy" if all(v == "up" for v in services.values()) else "degraded"

        if overall_status == "degraded":
            down = [k for k, v in services.items() if v == "down"]
            logger.warning(f"Health degraded — down: {', '.join(down)}")

        return Response({
            "success": overall_status == "healthy",
            "status": overall_status,
            "services": services
        }, status=200)

    def check_database(self):
        try:
            connection.ensure_connection()
            return "up"
        except Exception as e:
            logger.error(f"Database health failed: {e}")
            return "down"

    def check_redis(self):
        try:
            redis_client.ping()
            return "up"
        except Exception as e:
            logger.error(f"Redis health failed: {e}")
            return "down"

    def check_service(self, service_name):
        try:
            if service_name not in settings.SERVICE_URLS:
                logger.error(f"{service_name} missing in SERVICE_URLS")
                return "down"

            url = settings.SERVICE_URLS[service_name] + "/health"
            res = httpx.get(url, timeout=2)

            if res.status_code != 200:
                logger.warning(f"{service_name} returned {res.status_code}")
                return "down"

            return "up"

        except httpx.TimeoutException:
            logger.warning(f"{service_name} timed out")
            return "down"

        except httpx.RequestError as e:
            logger.error(f"{service_name} request failed: {e}")
            return "down"

        except Exception as e:
            logger.error(f"{service_name} unexpected error: {e}")
            return "down"


class NotificationProxy(APIView):
    """
    Gateway reverse proxy for Notification Service requests.
    """

    def get(self, request, *args, **kwargs):
        return self.handle(request)

    def post(self, request, *args, **kwargs):
        return self.handle(request)

    def put(self, request, *args, **kwargs):
        return self.handle(request)

    def patch(self, request, *args, **kwargs):
        return self.handle(request)

    def delete(self, request, *args, **kwargs):
        return self.handle(request)

    def handle(self, request):
        response = async_to_sync(proxy_request)(request, "NOTIFICATION")

        if not response:
            return Response(
                {"success": False, "message": "Notification Service unavailable"},
                status=503
            )

        return Response(response.json(), status=response.status_code)
