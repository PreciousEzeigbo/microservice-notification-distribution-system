import logging
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from django.http import JsonResponse

logger = logging.getLogger(__name__)

PUBLIC_PATHS = ["/api/v1/auth/login", "/api/v1/auth/register"]


class JWTMiddleware:
    """
    Django middleware for JWT authentication enforcement.

    Validates JWT tokens on all requests except public paths (login, register).
    Attaches authenticated user to request object or returns 401 for invalid tokens.

    Public paths bypass authentication. All other paths require valid JWT token
    in Authorization header (format: "Bearer <token>").
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.auth = JWTAuthentication()

    def __call__(self, request):
        # Skip authentication for public endpoints
        if any(request.path.startswith(p) for p in PUBLIC_PATHS):
            return self.get_response(request)

        # Authenticate request
        try:
            auth_result = self.auth.authenticate(request)
            if auth_result is not None:
                request.user, request.auth = auth_result
        except (InvalidToken, AuthenticationFailed) as e:
            logger.warning(f"JWT authentication failed for {request.path}: {str(e)}")
            return JsonResponse(
                {
                    "success": False,
                    "message": "Unauthorized",
                    "error": "Invalid or missing token",
                },
                status=401,
            )
        except Exception as e:
            logger.error(f"Unexpected error during JWT authentication: {str(e)}")
            return JsonResponse(
                {
                    "success": False,
                    "message": "Authentication error",
                    "error": "Internal server error",
                },
                status=500,
            )

        return self.get_response(request)
