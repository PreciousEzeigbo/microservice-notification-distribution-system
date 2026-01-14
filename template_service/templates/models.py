from django.db import models
import uuid

class Template(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)  # e.g., "welcome_email", "password_reset"
    subject = models.CharField(max_length=255)
    html_body = models.TextField()
    text_body = models.TextField(blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'templates'
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name