"""
Logging Configuration

Supports:
- Structured JSON logging for production
- Human-readable text logging for development
- Correlation IDs for request tracing
- Log levels per environment
"""

import json
import logging
import sys
from datetime import datetime
from typing import Optional

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    Used in production for log aggregation systems (ELK, CloudWatch, etc.)
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": settings.APP_NAME,
            "environment": settings.ENVIRONMENT,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id

        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        if hasattr(record, "notification_id"):
            log_data["notification_id"] = record.notification_id

        # Add custom fields from extra parameter
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
            ]:
                if not key.startswith("_"):
                    log_data[key] = value

        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """
    Human-readable text formatter for development.
    Includes colors for different log levels.
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

        # Build log message
        log_parts = [
            f"{color}{record.levelname:8}{reset}",
            f"[{timestamp}]",
            f"{record.name}:",
            record.getMessage(),
        ]

        # Add correlation ID if present
        if hasattr(record, "correlation_id"):
            log_parts.insert(2, f"[{record.correlation_id}]")

        log_message = " ".join(log_parts)

        # Add exception if present
        if record.exc_info:
            log_message += "\n" + self.formatException(record.exc_info)

        return log_message


def setup_logging():
    """
    Configure application logging.

    - Production: JSON format
    - Development: Human-readable text with colors
    """
    # Determine log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # Set formatter based on environment
    if settings.LOG_FORMAT == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("aio_pika").setLevel(logging.WARNING)
    logging.getLogger("aiormq").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: level={settings.LOG_LEVEL}, format={settings.LOG_FORMAT}")


def get_logger_with_context(
    name: str,
    correlation_id: Optional[str] = None,
    user_id: Optional[str] = None,
    notification_id: Optional[str] = None,
) -> logging.LoggerAdapter:
    """
    Get logger with contextual information.

    Usage:
        logger = get_logger_with_context(
            __name__,
            correlation_id="req-123",
            user_id="user-456"
        )
        logger.info("Processing request")  # Will include context
    """
    logger = logging.getLogger(name)

    extra = {}
    if correlation_id:
        extra["correlation_id"] = correlation_id
    if user_id:
        extra["user_id"] = user_id
    if notification_id:
        extra["notification_id"] = notification_id

    return logging.LoggerAdapter(logger, extra)
