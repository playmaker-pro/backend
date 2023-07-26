from django.contrib.auth import get_user_model
from drf_yasg import openapi
from rest_framework import serializers, status

from users.serializers import FeatureElementSerializer, FeaturesSerializer

User = get_user_model()


class UserRegisterResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration response.
    We want to exclude a password field from the swagger response.
    """

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "username"]


USER_LOGIN_ENDPOINT_SWAGGER_SCHEMA = dict(
    name="post",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "email": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="User email",
            ),
            "password": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="User super secret password.",
            ),
        },
        required=["email", "password"],
    ),
    responses={
        status.HTTP_200_OK: openapi.Response(
            description="User logged in successfully - tokens returned.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "access": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Access Token",
                    ),
                    "refresh": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Refresh Token",
                    ),
                },
                example={
                    "access": "some_super_secret_jwt_token",
                    "refresh": "refresh_token",
                },
            ),
        ),
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            description="Bad request",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "detail": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Detailed error message",
                    ),
                },
                example={
                    "detail": "No active account found with the given credentials"
                },
            ),
        ),
        status.HTTP_404_NOT_FOUND: openapi.Response(
            description="User not found with given credentials",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "detail": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Detailed error message",
                    ),
                },
                example={"detail": "Bad request"},
            ),
        ),
    },
)

USER_REGISTER_ENDPOINT_SWAGGER_SCHEMA = dict(
    name="post",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "email": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="User email",
            ),
            "password": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="User super secret password.",
            ),
            "first_name": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="User first name.",
            ),
            "last_name": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="User last name.",
            ),
        },
        required=["email", "password", "first_name", "last_name"],
    ),
    responses={
        status.HTTP_200_OK: openapi.Response(
            "User registered successfully.", UserRegisterResponseSerializer()
        ),
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            description="Bad request. Data sent in request is invalid.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "email": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Detailed error message",
                    ),
                    "first_name": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Detailed error message",
                    ),
                    "last_name": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Detailed error message",
                    ),
                    "password": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Detailed error message",
                    ),
                },
                example={
                    "email": ["This field is required."],
                    "first_name": ["This field is required."],
                    "last_name": ["This field is required."],
                    "password": ["This field is required."],
                },
            ),
        ),
    },
)

USER_FEATURE_SETS_SWAGGER_SCHEMA = dict(
    name="get",
    responses={
        status.HTTP_200_OK: openapi.Response(
            "User feature sets returned successfully.",
            FeaturesSerializer(),
        ),
        status.HTTP_404_NOT_FOUND: openapi.Response(
            "Feature sets for user not found",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "success": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Is response successful or not?",
                    ),
                    "detail": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Feature sets for user not found",
                    ),
                },
                example={
                    "success": "false",
                    "detail": "Feature sets for user not found",
                },
            ),
        ),
    },
)

USER_FEATURE_ELEMENTS_SWAGGER_SCHEMA = dict(
    name="get",
    responses={
        status.HTTP_200_OK: openapi.Response(
            "User feature sets returned successfully.",
            FeatureElementSerializer(),
        ),
        status.HTTP_404_NOT_FOUND: openapi.Response(
            "Feature elements for user not found",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "success": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Is response successful or not?",
                    ),
                    "detail": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Feature elements for user not found",
                    ),
                },
                example={
                    "success": "false",
                    "detail": "Feature elements for user not found",
                },
            ),
        ),
    },
)

USER_REFRESH_TOKEN_ENDPOINT_SWAGGER_SCHEMA = dict(
    name="post",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "refresh": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="User refresh token",
            ),
        },
        required=["refresh"],
    ),
    responses={
        status.HTTP_200_OK: openapi.Response(
            description="New token obtained successfully.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "access": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Access Token",
                    ),
                    "refresh": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Refresh Token",
                    ),
                },
                example={
                    "access": "some_super_secret_jwt_token",
                    "refresh": "refresh_token",
                },
            ),
        ),
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            description="Bad request",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "detail": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Detailed error message",
                    ),
                },
                example={"detail": "Refresh token is expired or invalid, respectively"},
            ),
        ),
        status.HTTP_401_UNAUTHORIZED: openapi.Response(
            description="Unauthorized request",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "detail": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Detailed error message",
                    ),
                },
                example={"detail": "Bad request"},
            ),
        ),
    },
)

GOOGLE_AUTH_SWAGGER_SCHEMA = dict(
    name="post",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "token_id": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Token id from Google.",
            ),
        },
        required=["token_id"],
    ),
    responses={
        status.HTTP_200_OK: openapi.Response(
            description="User logged in successfully - tokens returned.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "success": openapi.Schema(
                        type=openapi.TYPE_BOOLEAN,
                        description="Is request successful",
                    ),
                    "redirect": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="The page where user should be redirected. "
                        "Landing page after login, or register page if user is new."
                        "Choices: 'landing page', 'register'",
                    ),
                    "refresh_token": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="JWT refresh token.",
                    ),
                    "access_token": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="JWT access token.",
                    ),
                },
                example={
                    "success": True,
                    "redirect": "landing page",
                    "access": "some_super_secret_jwt_token",
                    "refresh": "refresh_token",
                },
            ),
        ),
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            description="Bad request",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "detail": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Detailed error message",
                    ),
                },
                example={
                    "detail": "No user credential fetched from Google. Please try again."
                },
            ),
        ),
    },
)
