from rest_framework import serializers
from .models import Template

class TemplateVariableExtractionSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)

class TemplateCompileSerializer(serializers.Serializer):
    variables = serializers.DictField(child=serializers.CharField())

class TemplateResponseSerializer(serializers.ModelSerializer):
    required_variables = serializers.SerializerMethodField()

    class Meta:
        model = Template
        fields = ['id', 'name', 'subject', 'html_body', 'text_body', 'required_variables', 'is_active']

    def get_required_variables(self, obj):
        from .services import extract_placeholders
        vars_set = extract_placeholders(obj.html_body)
        if obj.text_body:
            vars_set.update(extract_placeholders(obj.text_body))
        return sorted(list(vars_set))