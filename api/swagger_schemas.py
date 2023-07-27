from django.contrib.auth import get_user_model
from drf_yasg import openapi
from rest_framework import status, serializers

from users.serializers import FeaturesSerializer, FeatureElementSerializer

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

CITIES_VIEW_SWAGGER_SCHEMA = dict(
    name="get",
    operation_id="list_cities",
    operation_summary="Cities endpoint",
    manual_parameters=[
        openapi.Parameter(
            "city",
            openapi.IN_QUERY,
            description="City or voivodeship name to filter",
            type=openapi.TYPE_STRING,
        ),
    ],
    responses={
        status.HTTP_200_OK: openapi.Response(
            "List of [city, voivodeship] pairs returned successfully. For example: "
            '["Aleksandrów Łódzki", "Łódzkie"].',
            schema=openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                ),
            ),
        ),
    },
)

PREFERENCE_CHOICES_VIEW_SWAGGER_SCHEMA = dict(
    name="get",
    operation_id="list_preference_choices",
    operation_summary="User preferences endpoint",
    manual_parameters=[],
    responses={
        status.HTTP_200_OK: openapi.Response(
            "Preferences choices returned successfully.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "gender": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "value": openapi.Schema(type=openapi.TYPE_STRING),
                                "label": openapi.Schema(type=openapi.TYPE_STRING),
                            },
                        ),
                    ),
                    "player_preferred_leg": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "value": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "label": openapi.Schema(type=openapi.TYPE_STRING),
                            },
                        ),
                    ),
                },
            ),
        ),
    },
)

ROLES_API_SWAGGER_SCHEMA = dict(
    name="get",
    operation_id="list",
    operation_summary="Roles endpoint",
    responses={
        status.HTTP_200_OK: openapi.Response(
            "Available roles returned successfully.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                additionalProperties=openapi.Schema(type=openapi.TYPE_STRING),
                example={
                    "P": "Piłkarz",
                },
            ),
        ),
    },
)
