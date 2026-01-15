from django.contrib import admin
from .models import TemplateVersion,EmailTemplate


admin.register(EmailTemplate)

class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_type','is_active','version', 'updated_at')
    list_filter = ('template_type', 'is_active')
    search_fields = ('name', 'subject', 'description')
    readonly_fields = ('created_at', 'updated_at', 'version')

admin.register(TemplateVersion)

class TemplateVersionAdmin(admin.ModelAdmin):
    list_display = ('template', 'version_number', 'created_at', 'created_by')
    list_filter = ('template',)
    readonly_fields = ('created_at',)
