from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, UserPreference
from .serializers import UserSerializer
from .utils import api_response


class UserCreateView(APIView):
    """
    POST /api/v1/users/
    Creates a user and returns JWT tokens.
    """

    def post(self, request):
        data = request.data

        user = User.objects.create_user(
            email=data["email"],
            password=data["password"],
            name=data["name"],
            push_token=data.get("push_token"),
        )

        UserPreference.objects.create(
            user=user,
            email=data["preferences"]["email"],
            push=data["preferences"]["push"],
        )

        refresh = RefreshToken.for_user(user)

        serializer = UserSerializer(user)

        return api_response(
            success=True,
            message="User created successfully",
            data={
                "user": serializer.data,
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    POST /api/v1/auth/login
    """

    def post(self, request):
        user = authenticate(
            email=request.data["email"],
            password=request.data["password"],
        )

        if not user:
            return api_response(
                success=False,
                message="Invalid credentials",
                error="Authentication failed",
                status=401,
            )

        refresh = RefreshToken.for_user(user)

        return api_response(
            success=True,
            message="Login successful",
            data={
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
        )


class UserDetailView(APIView):
    """
    GET /api/v1/users/{user_id}
    Used by other services.
    """

    def get(self, request, user_id):
        user = User.objects.get(id=user_id)
        serializer = UserSerializer(user)

        return api_response(
            success=True,
            message="User fetched",
            data=serializer.data,
        )


class HealthCheckView(APIView):
    """
    GET /health
    """

    def get(self, request):
        return api_response(
            success=True,
            message="User Service is healthy",
        )
