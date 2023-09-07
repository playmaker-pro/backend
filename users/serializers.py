from typing import Dict, Optional

from django.contrib.auth import get_user_model
from rest_framework import serializers

from api.serializers import CitySerializer, CountrySerializer
from features.models import AccessPermission, Feature, FeatureElement
from profiles import serializers as profile_serializers
from profiles.serializers import ProfileEnumChoicesSerializer
from users.errors import UserRegisterException
from users.models import UserPreferences
from users.utils.api_utils import modify2custom_exception

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class UserPreferencesSerializer(serializers.ModelSerializer):
    age = serializers.IntegerField(read_only=True)
    localization = CitySerializer(required=False)
    spoken_languages = profile_serializers.LanguageSerializer(many=True, required=False)
    citizenship = CountrySerializer(many=True, required=False)
    gender = ProfileEnumChoicesSerializer(model=UserPreferences, required=False)

    class Meta:
        model = UserPreferences
        fields = "__all__"
        extra_kwargs = {
            "user": {"read_only": True},
        }

    def update(self, instance, validated_data):
        if spoken_languages := validated_data.pop(
            "spoken_languages", None
        ):  # noqa: 599
            instance.spoken_languages.set(spoken_languages)

        instance.save()
        return super().update(instance, validated_data)


class UserDataSerializer(serializers.ModelSerializer):
    """User serializer with basic user information"""

    userpreferences = UserPreferencesSerializer(required=False, partial=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "last_login",
            "last_activity",
            "userpreferences",
        ]
        depth = 1
        extra_kwargs = {
            "last_activity": {"read_only": True},
            "last_login": {"read_only": True},
            "id": {"read_only": True},
        }

    def update(self, instance, validated_data) -> User:
        """Override method to achieve nested update"""
        if userpreferences_data := validated_data.pop("userpreferences"):  # noqa: 599
            userpreferences_data["user"] = instance.pk
            userpreferences_serializer = UserPreferencesSerializer(
                instance.userpreferences, data=userpreferences_data, partial=True
            )
            if userpreferences_serializer.is_valid(raise_exception=True):
                userpreferences_serializer.save()
        return super().update(instance, validated_data)


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "password", "username"]
        extra_kwargs = {
            "id": {"read_only": True, "required": False},
            "username": {"read_only": True, "required": False},
            "first_name": {"required": False},
            "last_name": {"required": False},
            "email": {"required": True},
        }

    @staticmethod
    def validate_password(value):
        if len(value) < 8:
            raise UserRegisterException(
                fields={"password": "Password must be at least 8 characters long."}
            )
        return value

    def to_internal_value(self, data):
        """Override to_internal_value method to handle custom exceptions."""
        validated_data: Optional[dict] = None
        try:
            validated_data = super().to_internal_value(data)
        except serializers.ValidationError as e:
            modify2custom_exception(e)

        return validated_data


class AccessPermissionSerializer(serializers.ModelSerializer):
    """Serializer for access permission."""

    class Meta:
        model = AccessPermission
        fields = ("role", "access")


class FeatureElementSerializer(serializers.ModelSerializer):
    """Serializer for feature element."""

    access_permissions = AccessPermissionSerializer(many=True)

    class Meta:
        model = FeatureElement
        fields = ("name", "permissions", "access_permissions")


class FeaturesSerializer(serializers.ModelSerializer):
    """Serializer for features."""

    elements = FeatureElementSerializer(many=True)

    class Meta:
        model = Feature
        fields = ("name", "keyname", "elements", "enabled")


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def to_internal_value(self, data):
        """Override to_internal_value method to handle custom exceptions."""
        validated_data: Optional[dict] = None
        try:
            validated_data = super().to_internal_value(data)
        except serializers.ValidationError as e:
            modify2custom_exception(e)  # Use the function to raise the custom exception
        return validated_data


class CreateNewPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    confirm_new_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data: Dict[str, str]) -> Dict[str, str]:
        """
        Check that the new_password and confirm_new_password fields match.
        """
        if data["new_password"] != data["confirm_new_password"]:
            raise UserRegisterException(
                fields={"non_field_errors": "Passwords must match"}
            )
        return data

    def validate_new_password(self, password: str) -> str:
        """
        Validates the new password based on pre-defined criteria.
        """
        if len(password) < 8:
            raise UserRegisterException(
                fields={"password": "Password must be at least 8 characters long."}
            )
        return password

    def to_internal_value(self, data):
        """Override to_internal_value method to handle custom exceptions."""
        validated_data: Optional[dict] = None
        try:
            validated_data = super().to_internal_value(data)
        except serializers.ValidationError as e:
            modify2custom_exception(e)

        return validated_data
