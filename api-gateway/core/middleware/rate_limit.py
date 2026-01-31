import logging
from django.http import JsonResponse
from core.redis_client import redis_client

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """
    Django middleware for IP-based rate limiting using Redis.

    Limits requests to 100 per minute per IP address. Returns 429 status
    when limit is exceeded. Uses Redis for distributed rate limit tracking
    across multiple application instances.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get("REMOTE_ADDR")
        key = f"rate:{ip}"

        try:
            # Get current count
            count = redis_client.get(key)

            if count is None:
                # First request in window - set count to 1 with 60s expiry
                redis_client.setex(key, 60, 1)
                count = 1
            else:
                # Increment existing count
                count = int(count)
                if count >= 100:
                    logger.warning(f"Rate limit exceeded for IP: {ip}")
                    return JsonResponse(
                        {
                            "success": False,
                            "message": "Too many requests",
                            "error": "Rate limit exceeded",
                        },
                        status=429,
                    )
                redis_client.incr(key)
                count += 1

        except Exception as e:
            # Don't block requests if Redis fails
            logger.error(f"Rate limiting error for IP {ip}: {str(e)}")

        return self.get_response(request)
