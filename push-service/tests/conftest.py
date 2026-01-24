import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from app.core.cache.redis_client import RedisClient
from app.core.queue.consumer import RabbitMQConsumer
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client():
    """FastAPI test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis_mock = MagicMock(spec=RedisClient)
    redis_mock.connect = AsyncMock()
    redis_mock.disconnect = AsyncMock()
    redis_mock.check_and_set_idempotency = AsyncMock(return_value=True)
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock()
    redis_mock.delete = AsyncMock()
    return redis_mock


@pytest.fixture
def mock_rabbitmq():
    """Mock RabbitMQ consumer."""
    rabbitmq_mock = MagicMock(spec=RabbitMQConsumer)
    rabbitmq_mock.connect = AsyncMock()
    rabbitmq_mock.disconnect = AsyncMock()
    rabbitmq_mock.start_consuming = AsyncMock()
    return rabbitmq_mock


@pytest.fixture
def mock_fcm_service():
    """Mock FCM service."""
    fcm_mock = MagicMock()
    fcm_mock.send_notification = AsyncMock(
        return_value={"total": 2, "successful": 2, "failed": 0, "results": []}
    )
    return fcm_mock


@pytest.fixture
def sample_notification_request():
    """Sample notification request data."""
    return {
        "notification_type": "push",
        "user_id": "user-456",
        "template_code": "welcome_notification",
        "variables": {
            "name": "John Doe",
            "link": "https://example.com/welcome",
            "meta": {"action": "login"},
        },
        "request_id": "notif-123",
        "priority": 1,
        "metadata": {"language": "en", "category": "security"},
    }


@pytest.fixture
def sample_push_notification():
    """Sample push notification data."""
    return {
        "notification_id": "notif-123",
        "user_id": "user-456",
        "device_tokens": ["fcm_token_1", "fcm_token_2"],
        "platform": "fcm",
        "notification": {
            "title": "Welcome!",
            "body": "Hello John Doe, you have successfully logged in.",
            "image_url": None,
            "click_action": "https://example.com/welcome",
            "custom_data": {"category": "security", "type": "alert"},
        },
        "priority": "high",
        "ttl": 86400,
        "correlation_id": "notif-123",
    }


@pytest.fixture
def mock_web_push_service():
    """Mock Web Push service."""
    web_push_mock = MagicMock()
    web_push_mock.send_notification = AsyncMock(return_value={"success": True})
    return web_push_mock
