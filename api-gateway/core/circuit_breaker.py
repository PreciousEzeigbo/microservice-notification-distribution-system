import pybreaker

# Circuit breakers for managing service failures and preventing cascading issues.
#
# This dictionary maintains circuit breaker instances for each external service
# dependency in the notification system. Circuit breakers automatically open
# (stop requests) when a service experiences repeated failures, allowing it time
# to recover before resuming normal operations.
#
# Configuration:
#   - fail_max: Maximum consecutive failures before opening the circuit (5)
#   - reset_timeout: Seconds to wait before attempting to close the circuit (30)
#
# Services monitored:
#   - USER: User service for fetching user data and preferences
#   - TEMPLATE: Template service for retrieving notification templates
#   - NOTIFICATION: Notification delivery service for sending emails/push notifications
SERVICE_BREAKERS = {
    "USER": pybreaker.CircuitBreaker(fail_max=5, reset_timeout=30),
    "TEMPLATE": pybreaker.CircuitBreaker(fail_max=5, reset_timeout=30),
    "NOTIFICATION": pybreaker.CircuitBreaker(fail_max=5, reset_timeout=30),
}