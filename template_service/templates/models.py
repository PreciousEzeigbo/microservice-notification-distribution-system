from django.db import models
from django.core.validators import RegexValidator
import re
from .services import extract_placeholders as service_extract


class EmailTemplate(models.Model):
    """Email template model with Handlebars support"""
    
    TEMPLATE_TYPES = [
        ('welcome', 'Welcome Email'),
        ('reset_password', 'Password Reset'),
        ('notification', 'General Notification'),
        ('promotional', 'Promotional Email'),
        ('transactional', 'Transactional Email'),
    ]
    
    name = models.CharField(
        max_length=255,
        unique=True,
        validators=[
            RegexValidator(
                regex='^[a-z0-9_-]+$',
                message='Name must contain only lowercase letters, numbers, hyphens, and underscores'
            )
        ]
    )
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES)
    subject = models.CharField(max_length=500)
    html_content = models.TextField(help_text='HTML template with Handlebars placeholders')
    text_content = models.TextField(blank=True, help_text='Plain text version')
    
    # Metadata
    description = models.TextField(blank=True)
    required_variables = models.JSONField(
        default=list,
        help_text='List of required variable names'
    )
    optional_variables = models.JSONField(
        default=list,
        help_text='List of optional variable names'
    )
    
    # Status and versioning
    is_active = models.BooleanField(default=True)
    version = models.IntegerField(default=1)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=255, blank=True)
    
    class Meta:
        db_table = 'email_templates'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['template_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} (v{self.version})"
    
    def extract_placeholders(self):
        """Extract Handlebars placeholders from template content"""

        html_placeholders = service_extract(self.html_content)
        subject_placeholders = service_extract(self.subject)
        all_placeholders = html_placeholders | subject_placeholders
        return sorted(list(all_placeholders))

    
    def save(self, *args, **kwargs):
        """Auto-extract placeholders on save"""
        if not self.required_variables:
            self.required_variables = self.extract_placeholders()
        super().save(*args, **kwargs)


class TemplateVersion(models.Model):
    """Track template version history"""
    
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.CASCADE,
        related_name='versions'
    )
    version_number = models.IntegerField()
    html_content = models.TextField()
    text_content = models.TextField(blank=True)
    subject = models.CharField(max_length=500)
    required_variables = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=255, blank=True)
    change_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'template_versions'
        ordering = ['-version_number']
        unique_together = ['template', 'version_number']
    
    def __str__(self):
        return f"{self.template.name} - v{self.version_number}"