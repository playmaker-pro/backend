from typing import Optional

from django.contrib.auth import get_user_model
from rest_framework import serializers

from users.utils.api_utils import validate_serialized_email

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "password", "username"]
        extra_kwargs = {
            "id": {"read_only": True, "required": False},
            "username": {"read_only": True, "required": False},
            "first_name": {"required": True},
            "last_name": {"required": True},
            "email": {"required": True},
        }

    def to_internal_value(self, data):
        """Override to_internal_value method to handle custom exceptions."""
        validated_data: Optional[dict] = None
        try:
            validated_data = super().to_internal_value(data)
        except serializers.ValidationError as e:
            validate_serialized_email(e)

        return validated_data
