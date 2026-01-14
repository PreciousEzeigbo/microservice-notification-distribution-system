from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from .models import Template
from .serializers import TemplateResponseSerializer, TemplateCompileSerializer
from .services import compile_template, validate_required_variables
import logging

logger = logging.getLogger(__name__)

class TemplateDetailView(APIView):
    def get(self, request, name):
        template = get_object_or_404(Template, name=name, is_active=True)
        serializer = TemplateResponseSerializer(template)
        return Response(serializer.data)

class TemplateCompileView(APIView):
    def post(self, request, name):
        template = get_object_or_404(Template, name=name, is_active=True)

        serializer = TemplateCompileSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status_code": 400,
                "message": "Invalid payload",
                "error": "Bad Request",
                "details": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        variables = serializer.validated_data['variables']

        try:
            validate_required_variables(template, variables)
        except ValidationError as e:
            return Response({
                "status_code": 400,
                "message": str(e),
                "error": "Template Validation Error"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            compiled = compile_template(template.html_body, template.text_body, variables)
            subject = compile_template(template.subject, None, variables)

            return Response({
                "subject": subject["html"],
                "html": compiled["html"],
                "text": compiled["text"],
                "template_name": template.name
            })
        except Exception as e:
            logger.error(f"Template compilation failed for {name}: {e}")
            return Response({
                "status_code": 500,
                "message": "Template compilation failed",
                "error": "Internal Server Error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)