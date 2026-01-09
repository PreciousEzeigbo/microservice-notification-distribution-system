from rest_framework import status
from rest_framework.test import APITestCase

from .models import User, UserPreference


class UserServiceTests(APITestCase):
    """
    Test suite for User Service endpoints.
    """

    def setUp(self):
        """
        Runs before each test.
        Creates reusable test data.
        """
        self.signup_payload = {
            "name": "Test User",
            "email": "testuser@example.com",
            "password": "StrongPassword123",
            "push_token": "test_push_token",
            "preferences": {
                "email": True,
                "push": False
            }
        }

        self.login_payload = {
            "email": "testuser@example.com",
            "password": "StrongPassword123"
        }

    # ---------------------------------------------------
    # Health Check Test
    # ---------------------------------------------------
    def test_health_check(self):
        """
        GET /api/v1/health/
        """
        response = self.client.get("/api/v1/health/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["message"], "User Service is healthy")
        self.assertIsNone(response.data["error"])
        self.assertIsNone(response.data["meta"])

    # ---------------------------------------------------
    # User Signup Test
    # ---------------------------------------------------
    def test_user_signup(self):
        """
        POST /api/v1/users/
        """
        response = self.client.post(
            "/api/v1/users/",
            data=self.signup_payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])

        # Assert user data
        user_data = response.data["data"]["user"]
        self.assertEqual(user_data["email"], self.signup_payload["email"])
        self.assertEqual(user_data["name"], self.signup_payload["name"])
        self.assertIn("id", user_data)

        # Assert preferences
        preferences = user_data["preferences"]
        self.assertTrue(preferences["email"])
        self.assertFalse(preferences["push"])

        # Assert tokens
        tokens = response.data["data"]["tokens"]
        self.assertIn("access", tokens)
        self.assertIn("refresh", tokens)

        # Assert DB records
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(UserPreference.objects.count(), 1)

    # ---------------------------------------------------
    # Login Test
    # ---------------------------------------------------
    def test_user_login(self):
        """
        POST /api/v1/auth/login
        """
        # First create a user
        self.client.post(
            "/api/v1/users/",
            data=self.signup_payload,
            format="json"
        )

        response = self.client.post(
            "/api/v1/auth/login/",
            data=self.login_payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

        # Assert tokens
        tokens = response.data["data"]
        self.assertIn("access", tokens)
        self.assertIn("refresh", tokens)

    # ---------------------------------------------------
    # Get User by ID Test
    # ---------------------------------------------------
    def test_get_user_by_id(self):
        """
        GET /api/v1/users/{user_id}/
        """
        # Create user
        signup_response = self.client.post(
            "/api/v1/users/",
            data=self.signup_payload,
            format="json"
        )

        user_id = signup_response.data["data"]["user"]["id"]

        response = self.client.get(f"/api/v1/users/{user_id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

        user_data = response.data["data"]
        self.assertEqual(user_data["email"], self.signup_payload["email"])
        self.assertEqual(user_data["name"], self.signup_payload["name"])
        self.assertIn("preferences", user_data)


