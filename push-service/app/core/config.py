"""
Configuration Management
Uses Pydantic Settings for type-safe environment variable loading.
Supports multiple environments (dev, staging, production).
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

# Circuit Breaker constants (not configurable via environment variables)
CIRCUIT_BREAKER_EXPECTED_EXCEPTION = (Exception,)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses pydantic-settings for validation and type conversion.
    """

    APP_NAME: str = "Push Notification Service"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    HOST: str = "0.0.0.0"
    PORT: int = 8003
    WORKERS: int = 4

    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    RABBITMQ_EXCHANGE: str = "notifications.direct"
    RABBITMQ_PUSH_QUEUE: str = "push.queue"
    RABBITMQ_FAILED_QUEUE: str = "failed.queue"
    RABBITMQ_PREFETCH_COUNT: int = 10

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_CACHE_TTL: int = 3600
    REDIS_IDEMPOTENCY_SET: str = "idempotency_keys"
    REDIS_INVALID_TOKEN_SET: str = "invalid_tokens"

    # User Service Configuration (manages user contact info including push tokens)
    USER_SERVICE_URL: Optional[str] = None
    USER_SERVICE_TIMEOUT: float = 5.0
    USE_DUMMY_DEVICE_TOKENS: bool = True  # Set to False when user service is available

    # Template Service Configuration (handles template rendering and variable substitution)
    TEMPLATE_SERVICE_URL: Optional[str] = None
    TEMPLATE_SERVICE_TIMEOUT: float = 5.0
    USE_DUMMY_TEMPLATES: bool = True  # Set to False when template service is available

    FCM_ENABLED: bool = True
    FCM_CREDENTIALS_PATH: Optional[str] = None
    FCM_PROJECT_ID: Optional[str] = None

    WEB_PUSH_ENABLED: bool = True
    VAPID_PRIVATE_KEY: Optional[str] = None
    VAPID_PUBLIC_KEY: Optional[str] = None
    VAPID_SUBJECT: str = "mailto:admin@example.com"

    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60

    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_INITIAL_DELAY: float = 1.0
    RETRY_MAX_DELAY: float = 60.0
    RETRY_EXPONENTIAL_BASE: float = 2.0

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # CORS Configuration
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    CORS_ALLOW_CREDENTIALS: bool = True

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    @property
    def rabbitmq_url(self) -> str:
        """Construct RabbitMQ connection URL."""
        return (
            f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}"
            f"@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/{self.RABBITMQ_VHOST}"
        )

    @property
    def redis_url(self) -> str:
        """Construct Redis connection URL."""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance.
    Using lru_cache ensures we only create one instance.
    """
    return Settings()


settings = get_settings()
