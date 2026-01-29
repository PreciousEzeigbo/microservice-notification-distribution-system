import uuid


class CorrelationMiddleware:
    """
    Django middleware for correlation ID tracking across distributed requests.
    
    This middleware ensures every request has a unique correlation ID that can be
    used to trace the request flow across multiple services and components. It
    supports both client-provided correlation IDs (via X-Correlation-ID header)
    and auto-generation for requests without one.
    
    The correlation ID is:
    - Extracted from incoming X-Correlation-ID header if present
    - Auto-generated as a UUID4 if not provided by the client
    - Attached to the request object for use throughout the request lifecycle
    - Returned in the response X-Correlation-ID header for client tracking
    
    This enables:
    - End-to-end request tracing across microservices
    - Log correlation for debugging distributed systems
    - Client-side request tracking and monitoring
    - Support for distributed tracing tools
    
    Usage:
        Add to MIDDLEWARE in Django settings:
        MIDDLEWARE = [
            ...
            'path.to.CorrelationMiddleware',
            ...
        ]
    
    Attributes:
        get_response: Callable that processes the request through remaining middleware
                     and view layers
    
    Example:
        # Client sends request with correlation ID
        GET /api/notifications
        Headers: X-Correlation-ID: abc-123-def-456
        
        # Response includes same correlation ID
        Response Headers: X-Correlation-ID: abc-123-def-456
        
        # Request without correlation ID gets auto-generated one
        GET /api/users
        Response Headers: X-Correlation-ID: 550e8400-e29b-41d4-a716-446655440000
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        request.correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        response = self.get_response(request)
        response["X-Correlation-ID"] = request.correlation_id
        return response