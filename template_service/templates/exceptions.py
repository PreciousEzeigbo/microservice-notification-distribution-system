from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns snake_case responses
    matching the NestJS email service format
    """
    
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Customize the response format to match snake_case convention
        custom_response = {
            'status_code': response.status_code,
            'message': str(exc.detail) if hasattr(exc, 'detail') else 'An error occurred',
            'error': response.status_text if hasattr(response, 'status_text') else 'Error',
            'timestamp': timezone.now().isoformat(),
        }
        
        # Add validation errors if present
        if isinstance(response.data, dict):
            if 'detail' in response.data:
                custom_response['message'] = response.data['detail']
            else:
                custom_response['details'] = response.data
        
        return Response(custom_response, status=response.status_code)
    
    return response