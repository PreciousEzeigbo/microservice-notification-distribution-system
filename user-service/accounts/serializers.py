from rest_framework import serializers
from .models import User, UserPreference


class UserPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for user notification preferences.
    """

    class Meta:
        model = UserPreference
        fields = ("email", "push")


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer matching the UserData contract.
    """

    preferences = UserPreferenceSerializer()

    class Meta:
        model = User
        fields = (
            "id",
            "name",
            "email",
            "push_token",
            "preferences",
        )
