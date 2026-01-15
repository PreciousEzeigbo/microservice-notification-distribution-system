from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code in [200, 503]

    data = response.json()
    assert "success" in data
    assert "data" in data
    assert "status" in data["data"]
    assert "checks" in data["data"]
    assert "redis" in data["data"]["checks"]
    assert "rabbitmq" in data["data"]["checks"]


def test_health_endpoint_structure():
    """Test health check response structure."""
    response = client.get("/api/v1/health")
    data = response.json()

    assert isinstance(data["success"], bool)
    assert isinstance(data["data"]["status"], str)
    assert isinstance(data["data"]["checks"], dict)
    assert "status" in data["data"]["checks"]["redis"]
    assert "status" in data["data"]["checks"]["rabbitmq"]
