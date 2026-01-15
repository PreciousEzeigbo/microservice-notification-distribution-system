"""Tests for RabbitMQ Consumer."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.queue.consumer import RabbitMQConsumer


@pytest.fixture
def rabbitmq_consumer():
    """Create RabbitMQ consumer with mocked dependencies."""
    with patch("aio_pika.connect_robust"):
        consumer = RabbitMQConsumer()
        return consumer


@pytest.mark.asyncio
async def test_consumer_connect(rabbitmq_consumer):
    """Test consumer connection."""
    with patch("aio_pika.connect_robust", new=AsyncMock()) as mock_connect:
        mock_connect.return_value = MagicMock()
        await rabbitmq_consumer.connect()
        assert rabbitmq_consumer.connection is not None


@pytest.mark.asyncio
async def test_consumer_disconnect(rabbitmq_consumer):
    """Test consumer disconnection."""
    rabbitmq_consumer.connection = MagicMock()
    rabbitmq_consumer.connection.close = AsyncMock()
    await rabbitmq_consumer.disconnect()
    assert not rabbitmq_consumer.is_consuming
