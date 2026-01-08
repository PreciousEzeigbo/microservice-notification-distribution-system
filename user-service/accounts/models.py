import uuid
from django.db import models

# Base classes for building a custom Django user model
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """
    Custom user manager for the User model.

    Required when using AbstractBaseUser.
    Defines how users and superusers are created.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and return a regular user.
        """
        if not email:
            raise ValueError("Email is required")

        # Normalize email (lowercase domain, etc.)
        email = self.normalize_email(email)

        # Create user instance (extra_fields can include push_token, name, etc.)
        user = self.model(email=email, **extra_fields)

        # Hash and set password
        user.set_password(password)

        # Save user to database
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and return a superuser (admin).
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model for the User Service.

    - Uses UUID as primary key (microservice-safe)
    - Uses email instead of username
    """

    # Primary key as UUID for global uniqueness
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # User email (used for authentication)
    email = models.EmailField(unique=True)

    # User display name
    name = models.CharField(max_length=255)

    # Optional push notification token (FCM, Expo, etc.)
    push_token = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    # User status flags
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Attach custom user manager
    objects = UserManager()

    # Authentication configuration
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    def __str__(self):
        return self.email


class UserPreference(models.Model):
    """
    Stores notification preferences for a user.

    Kept separate to allow easy extension
    (SMS, WhatsApp, in-app notifications, etc.).
    """

    # One-to-one relationship with User
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="preferences"
    )

    # Whether the user wants email notifications
    email = models.BooleanField(default=True)

    # Whether the user wants push notifications
    push = models.BooleanField(default=True)

    def __str__(self):
        return f"Preferences for {self.user.email}"
