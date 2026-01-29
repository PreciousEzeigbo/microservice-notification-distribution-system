from django.contrib import admin
from django.utils.html import format_html

from observability.models import (
    GatewayRequestLog,
    NotificationAuditLog,
    ServiceFailureLog,
    GatewayMetrics
)


@admin.register(GatewayRequestLog)
class GatewayRequestLogAdmin(admin.ModelAdmin):
    """
    Admin interface for API Gateway request logs.
    Displays request metadata, routing targets, response codes,
    latency metrics, and correlation IDs for debugging and auditing.
    """

    list_display = (
        "method",
        "path",
        "status_code_colored",
        "latency_ms",
        "service_target",
        "user_id",
        "created_at"
    )

    search_fields = ("path", "correlation_id", "service_target", "user_id")
    list_filter = ("status_code", "method", "service_target", "created_at")

    readonly_fields = (
        "method",
        "path",
        "user_id",
        "status_code",
        "latency_ms",
        "service_target",
        "correlation_id",
        "created_at"
    )

    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_per_page = 50

    def status_code_colored(self, obj):
        color_map = {
            2: "green",
            3: "blue",
            4: "orange",
            5: "red",
        }
        status_class = obj.status_code // 100
        color = color_map.get(status_class, "black")

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.status_code
        )

    status_code_colored.short_description = "Status"
    status_code_colored.admin_order_field = "status_code"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(NotificationAuditLog)
class NotificationAuditLogAdmin(admin.ModelAdmin):
    """
    Admin interface for notification audit logs.
    Tracks notification lifecycle events, delivery status,
    template usage, and user association for compliance and debugging.
    """

    list_display = (
        "notification_id",
        "notification_type",
        "status_colored",
        "user_id",
        "template_code",
        "created_at"
    )

    search_fields = (
        "request_id",
        "notification_id",
        "correlation_id",
        "user_id",
        "template_code"
    )

    list_filter = ("status", "notification_type", "created_at")

    readonly_fields = (
        "notification_id",
        "request_id",
        "user_id",
        "notification_type",
        "template_code",
        "status",
        "correlation_id",
        "created_at"
    )

    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_per_page = 50

    def status_colored(self, obj):
        color_map = {
            "pending": "orange",
            "sent": "green",
            "failed": "red",
            "delivered": "blue",
        }

        color = color_map.get(obj.status, "black")

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.status
        )

    status_colored.short_description = "Status"
    status_colored.admin_order_field = "status"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(ServiceFailureLog)
class ServiceFailureLogAdmin(admin.ModelAdmin):
    """
    Admin interface for downstream service failure logs.
    Displays service outage events and error messages for incident analysis.
    """

    list_display = (
        "service_name",
        "error_message_short",
        "correlation_id",
        "created_at"
    )

    list_filter = ("service_name", "created_at")
    search_fields = ("service_name", "correlation_id", "error_message")

    readonly_fields = (
        "service_name",
        "error_message",
        "correlation_id",
        "created_at"
    )

    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_per_page = 50

    def error_message_short(self, obj):
        max_length = 80
        return (
            f"{obj.error_message[:max_length]}..."
            if obj.error_message and len(obj.error_message) > max_length
            else obj.error_message
        )

    error_message_short.short_description = "Error Message"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(GatewayMetrics)
class GatewayMetricsAdmin(admin.ModelAdmin):
    """
    Admin UI for Gateway service metrics.
    Safe against null values, SafeString formatting issues, and admin crashes.
    """

    list_display = (
        "service_name",
        "total_requests",
        "total_failures",
        "failure_rate_display",
        "avg_latency_ms_display",
        "last_updated"
    )

    readonly_fields = (
        "service_name",
        "total_requests",
        "total_failures",
        "avg_latency_ms",
        "last_updated"
    )

    ordering = ("service_name",)
    list_per_page = 20

    def failure_rate_display(self, obj):
        total = obj.total_requests or 0
        failures = obj.total_failures or 0

        if total == 0:
            return "0%"

        try:
            rate = (failures / total) * 100
        except Exception:
            return "N/A"

        color = "green" if rate < 5 else "orange" if rate < 15 else "red"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color,
            f"{rate:.2f}"
        )

    failure_rate_display.short_description = "Failure Rate"
    failure_rate_display.admin_order_field = None  # Prevent Django sorting bug

    def avg_latency_ms_display(self, obj):
        raw = obj.avg_latency_ms

        if raw in (None, "", "N/A"):
            return "N/A"

        try:
            value = float(raw)
        except Exception:
            return "N/A"

        color = "green" if value < 100 else "orange" if value < 500 else "red"

        return format_html(
            '<span style="color: {};">{} ms</span>',
            color,
            f"{value:.2f}"
        )

    avg_latency_ms_display.short_description = "Avg Latency"
    avg_latency_ms_display.admin_order_field = None  # Prevent Django sorting bug

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
