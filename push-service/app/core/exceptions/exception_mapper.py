from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions.custom_exceptions import (
    FCMServiceError,
    HealthServiceError,
    InvalidTokenError,
    NotificationServiceError,
    PushServiceError,
    WebPushServiceError,
)
from app.core.exceptions.error_status_map import ERROR_STATUS_MAP


def push_service_exception_handler(request: Request, exc: PushServiceError):
    return JSONResponse(
        status_code=exc.code if hasattr(exc, "code") else status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": exc.message,
            "data": None,
        },
    )


def fcm_service_exception_handler(request: Request, exc: FCMServiceError):
    return JSONResponse(
        status_code=exc.code if hasattr(exc, "code") else status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": exc.message,
            "data": None,
        },
    )


def web_push_service_exception_handler(request: Request, exc: WebPushServiceError):
    return JSONResponse(
        status_code=exc.code if hasattr(exc, "code") else status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": exc.message,
            "data": None,
        },
    )


def notification_service_exception_handler(request: Request, exc: NotificationServiceError):
    return JSONResponse(
        status_code=exc.code if hasattr(exc, "code") else status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": exc.message,
            "data": None,
        },
    )


def health_service_exception_handler(request: Request, exc: HealthServiceError):
    return JSONResponse(
        status_code=exc.code if hasattr(exc, "code") else status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": exc.message,
            "data": None,
        },
    )


def invalid_token_exception_handler(request: Request, exc: InvalidTokenError):
    return JSONResponse(
        status_code=exc.code if hasattr(exc, "code") else status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "message": exc.message,
            "data": None,
        },
    )


def service_exception_handler(request: Request, exc: Exception):
    status_code = ERROR_STATUS_MAP.get(type(exc), 500)
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": str(exc),
            "error_type": type(exc).__name__,
            "path": str(request.url),
        },
    )
