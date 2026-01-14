from django.db import models
from django.core.exceptions import ValidationError
import json

class Template(models.Model):
    id = models.CharField(max_length=36, primary_key=True)  # UUID string
    name = models.CharField(max_length=255)
    subject = models.TextField()
    content = models.TextField()                    # Handlebars template
    required_variables = models.JSONField(default=list)  # ["name", "order_id"]
    version = models.PositiveIntegerField(default=1)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if not self.required_variables:
            raise ValidationError("At least one variable is required")

    def __str__(self):
        return f"{self.name} (v{self.version})"