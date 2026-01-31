from django.urls import path
from core.views import (
    UserProxy,
    TemplateProxy,
    NotificationGateway,
    HealthCheck,
    NotificationProxy,
)

urlpatterns = [
    # User Service
    path("auth/", UserProxy.as_view()),
    path("auth/<path:path>", UserProxy.as_view()),
    path("users/", UserProxy.as_view()),
    path("users/<path:path>", UserProxy.as_view()),
    # Template Service
    path("templates/", TemplateProxy.as_view()),
    path("templates/<path:path>", TemplateProxy.as_view()),
    # Notification Service
    path("notifications/", NotificationGateway.as_view()),
    path("notifications/<path:path>", NotificationProxy.as_view()),
    # Health
    path("health/", HealthCheck.as_view()),
]
