from typing import Optional

from django.contrib.auth import get_user_model
from rest_framework import serializers

from api.serializers import CitySerializer, CountrySerializer
from profiles import serializers as profile_serializers
from profiles.serializers import ProfileEnumChoicesSerializer
from features.models import Feature, FeatureElement, AccessPermission
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
    localization = CitySerializer()
    spoken_languages = profile_serializers.LanguageSerializer(many=True)
    citizenship = CountrySerializer(many=True)
    gender = ProfileEnumChoicesSerializer(model=UserPreferences)

    class Meta:
        model = UserPreferences
        fields = "__all__"


class UserDataSerializer(serializers.ModelSerializer):
    """User serializer with basic user information"""

    userpreferences = UserPreferencesSerializer()

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
