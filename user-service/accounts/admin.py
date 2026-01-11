from django.contrib import admin
from .models import User, UserPreference


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "is_staff", "is_active")
    search_fields = ("email", "name")


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "email", "push")
    search_fields = ("user__email",)
