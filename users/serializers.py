from django.contrib.auth import get_user_model
from rest_framework import serializers

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
