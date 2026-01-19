from starlette import status

from app.core.exceptions.custom_exceptions import (
    FCMServiceError,
    HealthServiceError,
    InvalidTokenError,
    NotificationServiceError,
    PushServiceError,
    WebPushServiceError,
)

ERROR_STATUS_MAP = {
    FCMServiceError: status.HTTP_502_BAD_GATEWAY,
    NotificationServiceError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    PushServiceError: status.HTTP_502_BAD_GATEWAY,
    InvalidTokenError: status.HTTP_400_BAD_REQUEST,
    WebPushServiceError: status.HTTP_502_BAD_GATEWAY,
    HealthServiceError: status.HTTP_503_SERVICE_UNAVAILABLE,
}
