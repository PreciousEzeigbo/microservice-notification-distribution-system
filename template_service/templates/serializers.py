from rest_framework import serializers
from .models import EmailTemplate, TemplateVersion
import re


class EmailTemplateSerializer(serializers.ModelSerializer):
    """Serializer for EmailTemplate with snake_case fields"""
    
    template_type = serializers.CharField()
    html_content = serializers.CharField()
    text_content = serializers.CharField(required=False, allow_blank=True)
    required_variables = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    optional_variables = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    is_active = serializers.BooleanField(default=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    created_by = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = EmailTemplate
        fields = [
            'id',
            'name',
            'template_type',
            'subject',
            'html_content',
            'text_content',
            'description',
            'required_variables',
            'optional_variables',
            'is_active',
            'version',
            'created_at',
            'updated_at',
            'created_by',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at','version']
    
    def validate_name(self, value):
        """Validate template name format"""

        if not re.match(r'^[a-z0-9_-]+$', value):
            raise serializers.ValidationError(
                "Name must contain only lowercase letters, numbers, hyphens, and underscores"
            )
        return value
    
    def validate(self, data):
        """Validate template data"""
        # Extract placeholders from content
        html_content = data.get('html_content', '')
        subject = data.get('subject', '')
        
        if not html_content:
            raise serializers.ValidationError({
                'html_content': 'HTML content is required'
            })
        
        if not subject:
            raise serializers.ValidationError({
                'subject': 'Subject is required'
            })
        
        return data


class EmailTemplateListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    
    class Meta:
        model = EmailTemplate
        fields = [
            'id',
            'name',
            'template_type',
            'subject',
            'description',
            'is_active',
            'version',
            'created_at',
            'updated_at',
        ]


class TemplateVersionSerializer(serializers.ModelSerializer):
    """Serializer for template versions"""
    
    template_name = serializers.CharField(source='template.name', read_only=True)
    version_number = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = TemplateVersion
        fields = [
            'id',
            'template_name',
            'version_number',
            'html_content',
            'text_content',
            'subject',
            'required_variables',
            'created_at',
            'created_by',
            'change_notes',
        ]


class TemplateValidationSerializer(serializers.Serializer):
    """Serializer for template validation requests"""
    
    variables = serializers.DictField(
        required=True
    )
    
    def validate(self, data):
        """Validate that template exists and variables are sufficient"""
        template = self.context.get('template')
        
        if not template or not template.is_active:
            raise serializers.ValidationError({
                'template_name': f"Template not found or inactive"
            })
        
        # Check required variables
        provided_vars = data.get('variables', {})
        required_vars = set(template.required_variables)
        missing_vars = []

        for var_path in required_vars:
            keys = var_path.split('.')
            current_level = provided_vars
            found = True
            for key in keys:
                if not isinstance(current_level, dict) or key not in current_level:
                    found = False
                    break
                current_level = current_level[key]
            
            if not found:
                missing_vars.append(var_path)

        if missing_vars:
            raise serializers.ValidationError({
                'variables': f"Missing required variables: {', '.join(sorted(missing_vars))}"
            })
        return data