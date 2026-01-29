from observability.models import GatewayMetrics


def update_metrics(service_name, latency, failed=False):
    """
    Update performance metrics for a specific service.
    
    This function records request statistics for monitoring service health and
    performance. It tracks total requests, failures, and calculates a running
    average of response latency times.
    
    Args:
        service_name (str): Name of the service being monitored (e.g., 'USER', 'TEMPLATE')
        latency (float): Response time for the request in milliseconds
        failed (bool, optional): Whether the request failed. Defaults to False.
    
    Returns:
        None
    
    Side Effects:
        - Creates a new GatewayMetrics record if one doesn't exist for the service
        - Updates the existing metrics record with new request data
        - Persists changes to the database
    
    Note:
        The average latency is calculated as a simple moving average between
        the current average and the new latency value.
    """
    metrics, _ = GatewayMetrics.objects.get_or_create(service_name=service_name)
    metrics.total_requests += 1
    if failed:
        metrics.total_failures += 1
    metrics.avg_latency_ms = (metrics.avg_latency_ms + latency) / 2
    metrics.save()