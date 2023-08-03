from django.contrib.auth import get_user_model

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, OpenApiParameter
from drf_yasg import openapi
from rest_framework import serializers, status

from users.serializers import FeatureElementSerializer, FeaturesSerializer

User = get_user_model()


class UserRegisterResponseSerializer(serializers.ModelSerializer):
    """Serializer for user registration response."""

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "username"]


class UserLoginResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration response.
    We want to exclude a password field from the swagger response.
    """

    class Meta:
        model = User
        fields = ["email", "password"]


USER_LOGIN_ENDPOINT_SWAGGER_SCHEMA = dict(
    summary="User login endpoint",
    request={
        "schema": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "User email",
                },
                "password": {
                    "type": "string",
                    "description": "User super secret password.",
                },
            },
            "required": ["email", "password"],
        }
    },
    responses={
        status.HTTP_200_OK: {
            "type": "object",
            "properties": {
                "access": {
                    "type": "string",
                    "description": "Access Token",
                },
                "refresh": {
                    "type": "string",
                    "description": "Refresh Token",
                },
            },
            "example": {
                "access": "some_super_secret_jwt_token",
                "refresh": "refresh_token",
            },
            "description": "User logged in successfully - tokens returned.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "type": "object",
            "properties": {
                "detail": {
                    "type": "string",
                    "description": "Detailed error message",
                },
            },
            "example": {"detail": "No active account found with the given credentials"},
            "description": "Bad request",
        },
        status.HTTP_404_NOT_FOUND: {
            "type": "object",
            "properties": {
                "detail": {
                    "type": "string",
                    "description": "Detailed error message",
                },
            },
            "example": {"detail": "Bad request"},
            "description": "User not found with given credentials",
        },
    },
)

USER_REGISTER_ENDPOINT_SWAGGER_SCHEMA = dict(
    summary="User registration endpoint",
    request={
        "schema": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "User email",
                },
                "password": {
                    "type": "string",
                    "description": "User super secret password.",
                },
                "first_name": {"type": "string", "description": "User first name."},
                "last_name": {"type": "string", "description": "User last name."},
            },
            "required": ["email", "password"],
        }
    },
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=UserRegisterResponseSerializer,
            examples=[
                OpenApiExample(
                    "example1",
                    value={
                        "id": 1,
                        "email": "example_email@playmaker.com",
                        "first_name": "first_name",
                        "last_name": "last_name",
                        "username": "username",
                    },
                ),
            ],
        ),
        status.HTTP_400_BAD_REQUEST: {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "Detailed error message",
                },
                "password": {
                    "type": "string",
                    "description": "Detailed error message",
                },
            },
            "example": {
                "email": "Detailed error message",
                "password": "Detailed error message",
            },
            "description": "Bad request. Data sent in request is invalid.",
        },
    },
)

USER_FEATURE_SETS_SWAGGER_SCHEMA = dict(
    summary="User feature sets.",
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=FeaturesSerializer,
            description="Returns user feature sets. Returns empty list if user has no feature sets.",
        ),
    },
)

USER_FEATURE_ELEMENTS_SWAGGER_SCHEMA = dict(
    summary="User feature elements.",
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            description="Returns user feature elements. Returns empty list if user has no feature sets.",
            response=FeatureElementSerializer,
        ),
    },
)

USER_REFRESH_TOKEN_ENDPOINT_SWAGGER_SCHEMA = dict(
    summary="Refresh user token endpoint",
    request={
        "schema": {
            "type": "object",
            "properties": {
                "refresh": {
                    "type": "string",
                    "description": "User refresh token",
                },
            },
            "required": ["refresh"],
        }
    },
    responses={
        status.HTTP_200_OK: {
            "description": "New token obtained successfully.",
            "type": "object",
            "properties": {
                "access": {
                    "type": "string",
                    "description": "Access Token",
                },
                "refresh": {
                    "type": "string",
                    "description": "Refresh Token",
                },
            },
            "example": {
                "access": "some_super_secret_jwt_token",
                "refresh": "refresh_token",
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad request",
            "type": "object",
            "properties": {
                "detail": {
                    "type": "string",
                    "description": "Detailed error message",
                },
            },
            "example": {"detail": "Refresh token is expired or invalid, respectively"},
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized request",
            "type": "object",
            "properties": {
                "detail": {
                    "type": "string",
                    "description": "Detailed error message",
                },
            },
            "example": {"detail": "Bad request"},
        },
    },
)

GOOGLE_AUTH_SWAGGER_SCHEMA = dict(
    summary="Google auth endpoint",
    request={
        "schema": {
            "type": "object",
            "properties": {
                "token_id": {
                    "type": "string",
                    "description": "Token id from Google.",
                }
            },
            "required": ["token_id"],
        },
    },
    responses={
        status.HTTP_200_OK: {
            "description": "User logged in successfully - tokens returned.",
            "type": "object",
            "properties": {
                "success": {
                    "type": "boolean",
                    "description": "Is request successful",
                },
                "redirect": {
                    "type": "string",
                    "description": "The page where user should be redirected. "
                    "Landing page after login, or register page if user is new."
                    "Choices: 'landing page', 'register'",
                },
                "refresh_token": {
                    "type": "string",
                    "description": "JWT refresh token.",
                },
                "access_token": {
                    "type": "string",
                    "description": "JWT access token.",
                },
            },
            "example": {
                "success": True,
                "redirect": "landing page",
                "access": "some_super_secret_jwt_token",
                "refresh": "refresh_token",
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad request",
            "type": "object",
            "properties": {
                "detail": {
                    "type": "string",
                    "description": "Detailed error message",
                },
            },
            "example": {
                "detail": "No user credential fetched from Google. Please try again."
            },
        },
    },
)

CITIES_VIEW_SWAGGER_SCHEMA = dict(
    summary="List cities endpoint",
    parameters=[
        OpenApiParameter(
            name="city",
            location="query",
            description="City or voivodeship name to filter",
        )
    ],
    responses={
        status.HTTP_200_OK: {
            "type": "array",
            "description": "List of [city, voivodeship] pairs returned successfully. For example: "
            '["Aleksandrów Łódzki", "Łódzkie"].',
            "items": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "voivodeship": {"type": "string"},
                },
            },
        },
    },
)

PREFERENCE_CHOICES_VIEW_SWAGGER_SCHEMA = dict(
    summary="User preferences endpoint",
    responses={
        status.HTTP_200_OK: {
            "description": "Preferences choices returned successfully.",
            "type": "object",
            "properties": {
                "gender": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "value": {"type": "string"},
                            "label": {"type": "string"},
                        },
                    },
                },
                "player_preferred_leg": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "value": {"type": "integer"},
                            "label": {"type": "string"},
                        },
                    },
                },
            },
        },
    },
)


ROLES_API_SWAGGER_SCHEMA = dict(
    summary="Roles endpoint",
    responses={
        status.HTTP_200_OK: {
            "description": "Available roles returned successfully.",
            "type": "object",
            "properties": {
                "shortcut": {"type": "string"},
                "full_name": {"type": "string"},
            },
            "example": {
                "P": "Piłkarz",
            },
        },
    },
)

FORMATION_CHOICES_VIEW_SWAGGER_SCHEMA = dict(
    summary="Formations endpoint",
    description="Returns a dictionary where each key-value pair is a formation's unique string representation "
    "(like '4-4-2' or '4-3-3') mapped to its corresponding label.",
    responses={
        status.HTTP_200_OK: {
            "description": "Formation choices returned successfully.",
            "type": "object",
            "properties": {
                "shortcut": {"type": "string"},
                "full_name": {"type": "string"},
            },
            "example": {"4-4-2": "4-4-2", "4-3-3": "4-3-3"},
        },
    },
)
