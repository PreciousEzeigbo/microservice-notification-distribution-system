from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from .models import EmailTemplate, TemplateVersion
from .serializers import (
    EmailTemplateSerializer,
    EmailTemplateListSerializer,
    TemplateVersionSerializer,
    TemplateValidationSerializer,
)
import logging

logger = logging.getLogger(__name__)


class EmailTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing email templates
    Provides CRUD operations and additional template-specific actions
    """
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    lookup_field = 'name'
    
    def get_serializer_class(self):
        """Use lightweight serializer for list actions"""
        if self.action == 'list':
            return EmailTemplateListSerializer
        return EmailTemplateSerializer
    
    def get_queryset(self):
        """Filter templates based on query parameters"""
        queryset = EmailTemplate.objects.all()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by template type
        template_type = self.request.query_params.get('template_type')
        if template_type:
            queryset = queryset.filter(template_type=template_type)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Create a new template"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            template = serializer.save()
            
            # Create initial version
            TemplateVersion.objects.create(
                template=template,
                version_number=1,
                html_content=template.html_content,
                text_content=template.text_content,
                subject=template.subject,
                required_variables=template.required_variables,
                created_by=request.data.get('created_by', ''),
                change_notes='Initial version'
            )
        
        logger.info(f"Template created: {template.name}")
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Update template and create new version"""
        partial = kwargs.pop('partial', False)

        
        with transaction.atomic():
             # Use select_for_update to prevent race conditions
            instance = EmailTemplate.objects.select_for_update().get(name=kwargs.get('name'))
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
        
            instance.version += 1

            #save with explicit version to prevent client override
            template = serializer.save(version=instance.version)
            
            # Create version history
            TemplateVersion.objects.create(
                template=template,
                version_number=template.version,
                html_content=template.html_content,
                text_content=template.text_content,
                subject=template.subject,
                required_variables=template.required_variables,
                created_by=request.data.get('created_by', ''),
                change_notes=request.data.get('change_notes', 'Updated template')
            )
        
        logger.info(f"Template updated: {template.name} (v{template.version})")
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def versions(self, request, name=None):
        """Get all versions of a template"""
        template = self.get_object()
        versions = template.versions.all()
        serializer = TemplateVersionSerializer(versions, many=True)
        return Response({
            'template_name': template.name,
            'current_version': template.version,
            'versions': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def validate(self, request, name=None):
        """Validate template with provided variables"""
        template = self.get_object()
        
        serializer = TemplateValidationSerializer(
            data=request.data,
            context={'template': template}
        )
        
        serializer.is_valid(raise_exception=True)
        
        return Response({
            'valid': True,
            'template_name': template.name,
            'message': 'All required variables provided'
        })
    
    @action(detail=True, methods=['get'])
    def placeholders(self, request, name=None):
        """Extract and return all placeholders from template"""
        template = self.get_object()
        placeholders = template.extract_placeholders()
        
        return Response({
            'template_name': template.name,
            'placeholders': placeholders,
            'required_variables': template.required_variables,
            'optional_variables': template.optional_variables,
        })
    
    @action(detail=True, methods=['post'])
    def activate(self, request, name=None):
        """Activate a template"""
        template = self.get_object()
        template.is_active = True
        template.save()
        
        logger.info(f"Template activated: {template.name}")
        return Response({
            'message': f"Template '{template.name}' activated",
            'is_active': True
        })
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, name=None):
        """Deactivate a template"""
        template = self.get_object()
        template.is_active = False
        template.save()
        
        logger.info(f"Template deactivated: {template.name}")
        return Response({
            'message': f"Template '{template.name}' deactivated",
            'is_active': False
        })
    
    @action(detail=False, methods=['get'])
    def health(self, request):
        """Health check endpoint"""
        try:
            # Check database connection
            count = EmailTemplate.objects.count()
            
            return Response({
                'status': 'healthy',
                'timestamp': timezone.now().isoformat(),
                'database': {
                    'status': 'connected',
                    'templates_count': count
                }
            })
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return Response({
                'status': 'unhealthy',
                'error': 'Database connection failed'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        