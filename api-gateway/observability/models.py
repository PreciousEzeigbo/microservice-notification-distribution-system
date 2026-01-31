from django.db import models
import uuid


class GatewayRequestLog(models.Model):
    """
    Stores every request passing through the Gateway.
    Used for audit trails, debugging, and performance tracking.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    method = models.CharField(max_length=10)
    path = models.TextField()
    user_id = models.UUIDField(null=True, blank=True)
    status_code = models.IntegerField()
    latency_ms = models.FloatField()
    service_target = models.CharField(max_length=50)
    correlation_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)


class NotificationAuditLog(models.Model):
    """
    Tracks lifecycle of each notification request.
    Allows tracing from Gateway to delivery.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    notification_id = models.UUIDField()
    request_id = models.CharField(max_length=255)
    user_id = models.UUIDField()
    notification_type = models.CharField(max_length=20)
    template_code = models.CharField(max_length=100)
    status = models.CharField(max_length=20)
    correlation_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)


class ServiceFailureLog(models.Model):
    """
    Stores failures when downstream services are unavailable.
    Useful for debugging outages.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    service_name = models.CharField(max_length=50)
    error_message = models.TextField()
    correlation_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)


class GatewayMetrics(models.Model):
    """
    Aggregated performance metrics per service.
    Helps analyze system health over time.
    """

    service_name = models.CharField(max_length=50, unique=True)
    total_requests = models.PositiveIntegerField(default=0)
    total_failures = models.PositiveIntegerField(default=0)
    avg_latency_ms = models.FloatField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
