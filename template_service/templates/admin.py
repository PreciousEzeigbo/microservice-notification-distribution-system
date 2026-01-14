from django.contrib import admin
from .models import TemplateVersion,EmailTemplate


admin.site.register(TemplateVersion)
admin.site.register(EmailTemplate)
