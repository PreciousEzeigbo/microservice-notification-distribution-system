"""Tests for Device Token Client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.clients.device_token_client import DeviceTokenClient


@pytest.fixture
def device_token_client():
    """Create device token client instance."""
    with patch.object(DeviceTokenClient, "__init__", lambda self: None):
        client = DeviceTokenClient.__new__(DeviceTokenClient)
        client.base_url = "http://user-service:8001"
        return client


@pytest.mark.asyncio
async def test_get_tokens_success():
    """Test successful token retrieval from User Service."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json = MagicMock(return_value={"data": {"push_token": "fcm_token_123"}})

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        with patch("app.core.clients.device_token_client.settings") as mock_settings:
            mock_settings.USER_SERVICE_URL = "http://test"
            mock_settings.USER_SERVICE_TIMEOUT = 30
            mock_settings.USE_DUMMY_DEVICE_TOKENS = False

            client = DeviceTokenClient()
            tokens = await client.get_tokens_for_user("user123")
            assert len(tokens) == 1
            assert "fcm_token_123" in tokens


@pytest.mark.asyncio
async def test_get_tokens_fallback():
    """Test fallback to dummy tokens."""
    client = DeviceTokenClient()
    tokens = await client.get_tokens_for_user("user123")
    assert len(tokens) == 2
    assert "dummy" in tokens[0].lower()
