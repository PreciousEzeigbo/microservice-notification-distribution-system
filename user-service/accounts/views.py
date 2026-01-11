from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    LoginSerializer,
)
from .utils import api_response


class UserCreateView(APIView):
    """
    POST /api/v1/users/
    Creates a user and returns JWT tokens.
    """

    def post(self, request):
        # Validate and create user via serializer
        create_serializer = UserCreateSerializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)

        user = create_serializer.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        # Serialize response data
        response_serializer = UserSerializer(user)

        return api_response(
            success=True,
            message="User created successfully",
            data={
                "user": response_serializer.data,
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
    Authenticates a user and returns JWT tokens.
    """

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(**serializer.validated_data)

        if not user:
            return api_response(
                success=False,
                message="Invalid credentials",
                error="Authentication failed",
                status=status.HTTP_401_UNAUTHORIZED,
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
        user = get_object_or_404(User, id=user_id)
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
