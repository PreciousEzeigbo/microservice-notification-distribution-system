"""Integration tests for Push Service."""

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_check_integration():
    """Test health check endpoint integration."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

        assert response.status_code in [200, 503]
        data = response.json()

        assert "success" in data
        assert "data" in data
        assert "status" in data["data"]
        assert "checks" in data["data"]
        assert "redis" in data["data"]["checks"]
        assert "rabbitmq" in data["data"]["checks"]


@pytest.mark.asyncio
async def test_notification_status_endpoint():
    """Test notification status endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/push/status",
            json={
                "notification_id": "test-123",
                "status": "delivered",
                "details": {"message": "Successfully delivered"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "received" in data["message"].lower()
