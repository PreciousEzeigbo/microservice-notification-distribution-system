"""
Proxy Layer for API Gateway

Responsible for forwarding incoming gateway requests to downstream microservices.
Implements:
- Async HTTP forwarding via httpx
- Circuit breaker protection
- Metrics tracking
- Failure logging
- Correlation ID propagation
- Safe request forwarding with payload overrides
"""

import httpx
import time
import logging
from django.conf import settings
from core.circuit_breaker import SERVICE_BREAKERS
from core.metrics import update_metrics
from observability.models import ServiceFailureLog
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


async def proxy_request(request, service_name, override_body=None):
    """
    Async proxy layer that forwards the EXACT incoming request path
    to downstream services without modifying routes.
    """

    if service_name not in settings.SERVICE_URLS:
        logger.error(f"{service_name} missing from SERVICE_URLS")
        return None

    if service_name not in SERVICE_BREAKERS:
        logger.error(f"{service_name} missing from SERVICE_BREAKERS")
        return None

    service_url = settings.SERVICE_URLS[service_name]
    breaker = SERVICE_BREAKERS[service_name]
    start = time.time()
    correlation_id = getattr(request, "correlation_id", None)

    payload = override_body if override_body is not None else request.body

    async def call():
        async with httpx.AsyncClient(timeout=5) as client:

            # Forward the EXACT incoming path
            full_url = f"{service_url}{request.path}"

            # Append query params if present
            if request.META.get("QUERY_STRING"):
                full_url = f"{full_url}?{request.META['QUERY_STRING']}"

            headers = dict(request.headers)
            headers.pop("Host", None)
            headers.pop("Content-Length", None)

            logger.info(f"Forwarding → {service_name}: {full_url}")

            # JSON payload forwarding
            if isinstance(payload, dict):
                return await client.request(
                    method=request.method,
                    url=full_url,
                    headers=headers,
                    json=payload
                )

            # Raw body forwarding
            return await client.request(
                method=request.method,
                url=full_url,
                headers=headers,
                content=payload
            )

    try:
        response = await breaker.call_async(call)
        latency = (time.time() - start) * 1000

        await sync_to_async(update_metrics)(service_name, latency)

        request.service_target = service_name
        logger.info(f"Proxy success → {service_name} ({latency:.2f}ms)")
        return response

    except httpx.TimeoutException as e:
        latency = (time.time() - start) * 1000
        logger.warning(f"{service_name} timeout ({latency:.2f}ms): {e}")

        await sync_to_async(update_metrics)(service_name, latency, failed=True)
        await sync_to_async(ServiceFailureLog.objects.create)(
            service_name=service_name,
            error_message=f"Timeout: {e}",
            correlation_id=correlation_id
        )
        return None

    except httpx.RequestError as e:
        latency = (time.time() - start) * 1000
        logger.error(f"{service_name} request error ({latency:.2f}ms): {e}")

        await sync_to_async(update_metrics)(service_name, latency, failed=True)
        await sync_to_async(ServiceFailureLog.objects.create)(
            service_name=service_name,
            error_message=f"Request error: {e}",
            correlation_id=correlation_id
        )
        return None

    except Exception as e:
        latency = (time.time() - start) * 1000
        logger.exception(f"{service_name} unexpected error ({latency:.2f}ms): {e}")

        await sync_to_async(update_metrics)(service_name, latency, failed=True)
        await sync_to_async(ServiceFailureLog.objects.create)(
            service_name=service_name,
            error_message=f"Unexpected error: {e}",
            correlation_id=correlation_id
        )
        return None
