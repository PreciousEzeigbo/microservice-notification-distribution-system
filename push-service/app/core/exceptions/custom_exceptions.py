class ServiceError(Exception):
    """Base exception for all service-related errors."""

    def __init__(self, message: str = "Service error", code: int = 500):
        self.message = message
        self.code = code
        super().__init__(self.message)


class HealthServiceError(ServiceError):
    """Exception raised for errors in the Health service."""

    def __init__(self, message: str = "Health Service error", code: int = 500):
        super().__init__(message, code)


class WebPushServiceError(ServiceError):
    """Exception raised for errors in the Web Push service."""

    def __init__(self, message: str = "Web Push Service error", code: int = 500):
        super().__init__(message, code)


# Custom exceptions for notification services


class FCMServiceError(ServiceError):
    """Exception raised for errors in the FCM service."""

    def __init__(self, message: str = "FCM Service error", code: int = 500):
        super().__init__(message, code)


class NotificationServiceError(ServiceError):
    """Exception raised for errors in the Notification service."""

    def __init__(self, message: str = "Notification Service error", code: int = 500):
        super().__init__(message, code)


class PushServiceError(ServiceError):
    """Exception raised for errors in the Push service."""

    def __init__(self, message: str = "Push Service error", code: int = 500):
        super().__init__(message, code)


class InvalidTokenError(ServiceError):
    """Exception raised for invalid device tokens."""

    def __init__(self, message: str = "Invalid device token", code: int = 400):
        super().__init__(message, code)
