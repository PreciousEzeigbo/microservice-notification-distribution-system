import pytest
from unittest.mock import patch
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestGatewayHealth:
    def test_health_check_returns_200(self):
        client = APIClient()
        res = client.get("/api/v1/health/")

        assert res.status_code == 200
        assert "services" in res.data


@pytest.mark.django_db
class TestUserProxy:
    @patch("core.proxy.proxy_request")
    def test_user_service_down_returns_503(self, mock_proxy):
        mock_proxy.return_value = None

        client = APIClient()
        res = client.get("/api/v1/users/me/")

        assert res.status_code == 503
        assert res.data["success"] is False


@pytest.mark.django_db
class TestTemplateProxy:
    @patch("core.proxy.proxy_request")
    def test_template_service_down_returns_503(self, mock_proxy):
        mock_proxy.return_value = None

        client = APIClient()
        res = client.get("/api/v1/templates/")

        assert res.status_code == 503
        assert res.data["success"] is False


@pytest.mark.django_db
class TestNotificationGatewayValidation:
    def test_notification_missing_required_fields_returns_400(self):
        client = APIClient()

        # Send invalid payload (missing required fields)
        payload = {"notification_type": "email"}

        res = client.post("/api/v1/notifications/", payload, format="json")

        assert res.status_code == 400

        # Confirm serializer error keys exist
        assert "request_id" in res.data
        assert "template_code" in res.data


@pytest.mark.django_db
class TestNotificationServiceProxyDown:
    @patch("core.proxy.proxy_request")
    def test_notification_service_down_graceful(self, mock_proxy):
        # Simulate service down
        mock_proxy.return_value = None

        client = APIClient()
        res = client.get("/api/v1/notifications/history/")

        assert res.status_code == 503
        assert res.data["success"] is False
        assert "unavailable" in res.data["message"].lower()
