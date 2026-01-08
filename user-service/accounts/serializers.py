from rest_framework import serializers
from .models import User, UserPreference


class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = ("email", "push")


class UserSerializer(serializers.ModelSerializer):
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
