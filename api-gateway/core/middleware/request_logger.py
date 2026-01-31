import time
import logging
from asgiref.sync import sync_to_async, iscoroutinefunction
from observability.models import GatewayRequestLog

logger = logging.getLogger(__name__)


class RequestLoggerMiddleware:
    """
    Django middleware for logging all gateway requests with performance metrics.

    Records comprehensive request/response data including method, path, user,
    status code, latency, target service, and correlation ID for monitoring,
    debugging, and analytics purposes.

    Supports both sync and async views automatically. Creates database records
    for structured request logging while application loggers handle event-level
    logging (errors, warnings, debug messages).

    This middleware provides:
    - Performance monitoring (latency tracking per request)
    - User activity auditing (who accessed what)
    - Service routing tracking (which backend service handled the request)
    - Correlation-based distributed tracing

    Complements application logging:
    - Request Logger (this): Structured DB records of request metadata
    - Application Loggers: Event messages for debugging and monitoring
    - Both work together for complete observability

    Performance consideration:
    - Creates one DB write per request (high traffic = high DB load)
    - Consider batching, sampling, or async task queues for production scale
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.async_mode = iscoroutinefunction(get_response)

    def __call__(self, request):
        if self.async_mode:
            return self.__acall__(request)
        return self.__sync_call__(request)

    def __sync_call__(self, request):
        """Handle synchronous views"""
        start = time.time()
        response = self.get_response(request)
        latency = (time.time() - start) * 1000

        self._log_request(request, response, latency)
        return response

    async def __acall__(self, request):
        """Handle asynchronous views"""
        start = time.time()
        response = await self.get_response(request)
        latency = (time.time() - start) * 1000

        await self._log_request_async(request, response, latency)
        return response

    def _log_request(self, request, response, latency):
        """Synchronous logging"""
        correlation_id = getattr(request, "correlation_id", None)

        try:
            GatewayRequestLog.objects.create(
                method=request.method,
                path=request.path,
                user_id=getattr(request.user, "id", None)
                if hasattr(request, "user")
                else None,
                status_code=response.status_code,
                latency_ms=latency,
                service_target=getattr(request, "service_target", "unknown"),
                correlation_id=correlation_id,
            )
        except Exception as e:
            logger.error(
                f"Failed to create request log: {str(e)}",
                extra={
                    "path": request.path,
                    "method": request.method,
                    "correlation_id": correlation_id,
                },
            )

    async def _log_request_async(self, request, response, latency):
        """Asynchronous logging"""
        correlation_id = getattr(request, "correlation_id", None)

        try:
            await sync_to_async(GatewayRequestLog.objects.create)(
                method=request.method,
                path=request.path,
                user_id=getattr(request.user, "id", None)
                if hasattr(request, "user")
                else None,
                status_code=response.status_code,
                latency_ms=latency,
                service_target=getattr(request, "service_target", "unknown"),
                correlation_id=correlation_id,
            )
        except Exception as e:
            logger.error(
                f"Failed to create request log: {str(e)}",
                extra={
                    "path": request.path,
                    "method": request.method,
                    "correlation_id": correlation_id,
                },
            )
