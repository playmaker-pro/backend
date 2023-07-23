from drf_yasg import openapi
from rest_framework import status


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
