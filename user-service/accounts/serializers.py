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
    Read-only serializer matching the UserData response contract.
    Used for responses (GET user, signup response).
    """

    preferences = UserPreferenceSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "name",
            "email",
            "push_token",
            "preferences",
        )


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for validating and creating a new user.
    Used only for signup input.
    """

    preferences = UserPreferenceSerializer()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "name",
            "push_token",
            "preferences",
        )

    def create(self, validated_data):
        preferences_data = validated_data.pop("preferences")

        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            name=validated_data["name"],
            push_token=validated_data.get("push_token"),
        )

        UserPreference.objects.create(
            user=user,
            **preferences_data,
        )

        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for login validation.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
