"""
Main FastAPI Application

This is the entry point for the Push Service.
Handles:
- Application lifecycle (startup/shutdown)
- Background task management (queue consumer)
- API routing
- Middleware configuration
- Error handling
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.api.modules.v1.models.push_model import ApiResponse
from app.api.modules.v1.routes import health, notifications
from app.api.modules.v1.services.fcm_service import fcm_service
from app.core.cache.redis_client import redis_client
from app.core.config import settings
from app.core.exceptions.custom_exceptions import (
    FCMServiceError,
    HealthServiceError,
    PushServiceError,
    ServiceError,
    WebPushServiceError,
)
from app.core.exceptions.exception_mapper import (
    fcm_service_exception_handler,
    health_service_exception_handler,
    push_service_exception_handler,
    service_exception_handler,
    web_push_service_exception_handler,
)
from app.core.logging import setup_logging
from app.core.queue.consumer import rabbitmq_consumer

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    try:
        logger.info("Connecting to Redis...")
        await redis_client.connect()

        logger.info("Connecting to RabbitMQ...")
        await rabbitmq_consumer.connect()

        logger.info("Starting message consumer...")
        consumer_task = asyncio.create_task(rabbitmq_consumer.start_consuming())

        logger.info("✓ Push Service started successfully")
        logger.info(f"Listening on {settings.HOST}:{settings.PORT}")

        yield

    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise

    finally:
        logger.info("Shutting down Push Service...")

        await rabbitmq_consumer.stop_consuming()

        if "consumer_task" in locals():
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                pass

        await rabbitmq_consumer.disconnect()
        await redis_client.disconnect()
        await fcm_service.close()

        logger.info("✓ Push Service stopped gracefully")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Push Notification Service with FCM and Web Push support",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

allowed_origins = (
    settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else ["http://localhost:3000"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and responses."""
    logger.info(f"→ {request.method} {request.url.path}")

    try:
        response = await call_next(request)
        logger.info(f"← {request.method} {request.url.path} - Status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"✗ {request.method} {request.url.path} - Error: {type(e).__name__}: {str(e)}")
        raise


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    # Sanitize errors to remove sensitive 'input' field
    sanitized_errors = [
        {"loc": err["loc"], "msg": err["msg"], "type": err["type"]}
        for err in exc.errors()
    ]

    logger.warning(f"Validation error: {sanitized_errors}")

    response = ApiResponse(
        success=False,
        error="Validation error",
        message="Invalid request data",
        data={"errors": sanitized_errors},
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=response.model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}", exc_info=True)

    response = ApiResponse(
        success=False,
        error="Internal server error",
        message="An unexpected error occurred",
        data=None,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=response.model_dump()
    )


app.include_router(health.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.add_exception_handler(ServiceError, service_exception_handler)
app.add_exception_handler(PushServiceError, push_service_exception_handler)
app.add_exception_handler(FCMServiceError, fcm_service_exception_handler)
app.add_exception_handler(WebPushServiceError, web_push_service_exception_handler)
app.add_exception_handler(HealthServiceError, health_service_exception_handler)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "running",
    }


@app.get("/metrics", tags=["monitoring"])
async def metrics():
    """Get service metrics (Prometheus format optional)."""
    from app.api.modules.v1.services.push_service import push_service

    metrics_data = push_service.get_metrics()

    return ApiResponse(success=True, data=metrics_data, message="Metrics retrieved successfully")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.DEBUG,
    )
