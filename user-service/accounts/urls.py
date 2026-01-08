from django.urls import path
from .views import (
    UserCreateView,
    LoginView,
    UserDetailView,
    HealthCheckView,
)

urlpatterns = [
    path("users/", UserCreateView.as_view()), # User registration endpoint
    path("users/<uuid:user_id>/", UserDetailView.as_view()), # Fetch user details endpoint
    path("auth/login/", LoginView.as_view()), # User login endpoint
    path("health/", HealthCheckView.as_view()), # Health check endpoint
]
