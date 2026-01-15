class ServiceException(Exception):
    """Base exception for all service-related errors."""

    def __init__(self, message: str = "Service error", code: int = 500):
        self.message = message
        self.code = code
        super().__init__(self.message)


class HealthServiceException(Exception):
    """Exception raised for errors in the Health service."""

    def __init__(self, message: str = "Health Service error", code: int = 500):
        self.message = message
        self.code = code
        super().__init__(self.message)


class WebPushServiceException(Exception):
    """Exception raised for errors in the Web Push service."""

    def __init__(self, message: str = "Web Push Service error", code: int = 500):
        self.message = message
        self.code = code
        super().__init__(self.message)


# Custom exceptions for notification services


class FCMServiceException(Exception):
    """Exception raised for errors in the FCM service."""

    def __init__(self, message: str = "FCM Service error", code: int = 500):
        self.message = message
        self.code = code
        super().__init__(self.message)


class NotificationServiceException(Exception):
    """Exception raised for errors in the Notification service."""

    def __init__(self, message: str = "Notification Service error", code: int = 500):
        self.message = message
        self.code = code
        super().__init__(self.message)


class PushServiceException(Exception):
    """Exception raised for errors in the Push service."""

    def __init__(self, message: str = "Push Service error", code: int = 500):
        self.message = message
        self.code = code
        super().__init__(self.message)


class InvalidTokenException(Exception):
    """Exception raised for invalid device tokens."""

    def __init__(self, message: str = "Invalid device token", code: int = 400):
        self.message = message
        self.code = code
        super().__init__(self.message)
