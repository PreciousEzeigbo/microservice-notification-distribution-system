from starlette import status

from app.core.exceptions.custom_exceptions import (
    FCMServiceException,
    HealthServiceException,
    InvalidTokenException,
    NotificationServiceException,
    PushServiceException,
    WebPushServiceException,
)

ERROR_STATUS_MAP = {
    FCMServiceException: status.HTTP_502_BAD_GATEWAY,
    NotificationServiceException: status.HTTP_500_INTERNAL_SERVER_ERROR,
    PushServiceException: status.HTTP_502_BAD_GATEWAY,
    InvalidTokenException: status.HTTP_400_BAD_REQUEST,
    WebPushServiceException: status.HTTP_502_BAD_GATEWAY,
    HealthServiceException: status.HTTP_503_SERVICE_UNAVAILABLE,
}
