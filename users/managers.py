import logging
import traceback
from datetime import datetime as dt
from datetime import timedelta
from typing import Optional, Union

import requests
from allauth.socialaccount.models import SocialApp
from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _
from pydantic import ValidationError
from requests import Response

from backend.settings import cfg
from users.schemas import (
    GoogleSdkLoginCredentials,
    SocialAppPydantic,
    UserFacebookDetailPydantic,
    UserGoogleDetailPydantic,
)

logger = logging.getLogger(__name__)


class SocialAppManager:
    @staticmethod
    def get_social_app(provider: str) -> Optional[SocialAppPydantic]:
        """Get social app by provider. Returns custom pydantic object."""
        try:
            instance: SocialApp = SocialApp.objects.get(provider=provider)
            return SocialAppPydantic(
                client_id=instance.client_id, client_secret=instance.secret
            )
        except ObjectDoesNotExist:
            return None


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """

    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_("The Email must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self.create_user(email, password, **extra_fields)

    def last_login_users_days(self, days: int = 30):
        return self.filter(last_login__gt=dt.now() - timedelta(days=days))

    def players(self):
        return self.filter(declared_role="P")


class SocialAuthMixin:
    """
    Provides a mixin for requesting user data from a social authentication provider.

    This mixin encapsulates the functionality of sending a request to a social authentication
    provider's API to obtain user information. It handles the process of accessing user data
    using an authentication token.
    """  # noqa: E501

    URL: str = ""
    token_id: str = ""
    USER_DATA_SCOPE: str = ""

    def request_user_data(self) -> dict:
        """Returns user info from social auth provider. Raises ValueError if response is not ok."""  # noqa: E501

        user_data_params = {
            "access_token": self.token_id,
        }

        if self.USER_DATA_SCOPE:
            user_data_params["fields"] = self.USER_DATA_SCOPE

        response: Response = requests.get(self.URL, params=user_data_params)

        if not response.ok:
            error: Union[str, dict] = response.json().get("error")
            error_description: str = response.json().get("error_description")
            raise ValueError(
                f"{error if error_description else 'Error'}. "
                f"Reason: {error_description if error_description else error.get('message')}"
            )

        return response.json()


class GoogleManager(SocialAuthMixin):
    """
    GoogleManager class provides an interface for managing Google OAuth2 interactions using the Google OAuth2 SDK.

    This class encapsulates functionality related to user authentication and retrieval of user information
    from Google services. It serves as an abstraction layer for handling OAuth2 token management and user data.

    Attributes:
        URL (str): The URL for accessing user information via the OAuth2 protocol.

    Args:
        token_id (str): A unique identifier associated with the user's authentication token.

    """  # noqa: E501

    URL = "https://www.googleapis.com/oauth2/v3/userinfo"

    def __init__(self, token_id: str):
        self.token_id = token_id

    @staticmethod
    def google_sdk_login_get_credentials() -> GoogleSdkLoginCredentials:
        """Get Google credentials from DB and settings."""
        # TODO not used right now. Have to be removed in future.
        google: Optional[SocialAppPydantic] = SocialAppManager.get_social_app(
            provider="google"
        )

        if not google:
            msg = "Google provider is missing in DB."
            logger.critical(msg)
            raise ImproperlyConfigured(msg)

        client_id: str = google.client_id
        client_secret: str = google.client_secret
        project_id: str = settings.GOOGLE_OAUTH2_PROJECT_ID

        if not client_id:
            msg = "Google oauth2 client id missing in DB."
            logger.critical(str(traceback.format_exc()) + f"\n{msg}")
            raise ImproperlyConfigured(msg)

        if not client_secret:
            msg = "Google oauth2 client secret key missing in DB."
            logger.critical(str(traceback.format_exc()) + f"\n{msg}")
            raise ImproperlyConfigured(msg)

        if not project_id:
            msg = "Google oauth2 project id missing in settings."
            logger.critical(str(traceback.format_exc()) + f"\n{msg}")
            raise ImproperlyConfigured(msg)

        credentials = GoogleSdkLoginCredentials(
            client_id=client_id, client_secret=client_secret, project_id=project_id
        )

        return credentials

    def get_user_info(self) -> UserGoogleDetailPydantic:
        """
        Returns user info from Google as UserGoogleDetailPydantic instance.
        Example response from Google:
        {
        "sub": "123456789012345678901" (string),
        "name": "Test User" (string),
        "given_name": "Test" (string),
        "family_name": "User" (string),
        "picture": "example_url" (string),
        "email": user_email (string),
        "email_verified": True (bool),
        "locale": "pl" (string),
        }
        """
        data: dict = self.request_user_data()
        try:
            return UserGoogleDetailPydantic(**data)
        except ValidationError as e:
            logger.exception(str(e))
            raise ValueError(e)


class FacebookManager(SocialAuthMixin):
    """
    Manages interactions with the Facebook Graph API for user authentication and data retrieval.

    This class acts as an interface to the Facebook Graph API, handling user authentication and
    obtaining user information from Facebook services. It encapsulates the process of accessing
    user data using the specified token.

    Attributes:
        URL (str): The URL for accessing the Facebook Graph API.
        USER_DATA_SCOPE (str): The scope of user data to be retrieved.

    Args:
        token_id (str): Unique identifier associated with the user's authentication token.
    """  # noqa: E501

    def __init__(self, token_id: str):
        self.token_id = token_id

    URL = f"https://graph.facebook.com/{settings.FACEBOOK_GRAPH_API_VERSION}/me"
    USER_DATA_SCOPE: str = "id,name,email"

    def get_user_info(self) -> UserFacebookDetailPydantic:
        """Get user info from Facebook as UserFacebookDetailPydantic instance.
        Example response from facebook:
        {
        "id": "123456789012345678901" (string),
        "name": "Test User" (string),
        "email": user_email (string),
        }
        """
        data: dict = self.request_user_data()

        data["given_name"] = data.get("name", "").split(" ")[0]
        data["family_name"] = data.get("name", "").split(" ")[-1]

        try:
            return UserFacebookDetailPydantic(**data)
        except ValidationError as e:
            logger.exception(str(e))
            raise ValueError(e)


class UserTokenManager:
    """
    Utility class to manage user tokens for password reset.
    """

    success_message = "Password reset successful."
    error_message = "Something went wrong. Please try again later."

    @staticmethod
    def create_url(user: "User") -> str:
        """
        Generates a URL containing a token for the given user.
        Returns a complete URL containing the token for the user.

        TODO: Future Enhancements
        - Ensure the randomness of the link is sufficient according to the
        latest security standards.
        - Review and possibly shorten the token expiration time to enhance security,
        e.g., set to 1 hour.
        - Consider implementing one-time use tokens that get invalidated after
         a single use, to further secure the process against potential email leaks.
         Reference:
         https://niebezpiecznik.pl/post/najczestsze-bledy-programistow-w-formularzu-resetu-hasla/
        """
        uidb: str = urlsafe_base64_encode(force_bytes(user.id))
        token: str = default_token_generator.make_token(user)

        # The frontend base URL and the new password reset path
        base_url = cfg.webapp.url
        password_reset_path = "nowe-haslo"

        # Construct the full URL with query parameters
        reset_url = f"{base_url}{password_reset_path}?uidb64={uidb}&token={token}"
        return reset_url

    @staticmethod
    def create_email_verification_url(user: "User") -> str:
        """
        Generates a URL for email verification containing a unique token and user ID.

        This method creates a secure, unique URL intended for verifying
        a user's email address.
        It encodes the user's primary key (PK) and generates a token, appending
        both as query parameters to a predefined URL path for email verification.
        The URL is constructed using the frontend base URL and a specific
        path for email verification.
        """
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # The frontend base URL and the new password reset path
        base_url = cfg.webapp.url
        email_verify_path = "zweryfikuj-email"

        # Construct verification URL
        verification_url = (
            f"{base_url}{email_verify_path}?uidb64={uidb64}&token={token}"
        )
        return verification_url

    @staticmethod
    def is_token_valid(user: "User", token: str) -> bool:
        """
        Checks if the provided token is valid for the given user.

        This method uses the default token generator to verify the token's validity.
        It is intended to validate tokens typically used in password reset or email
        verification processes.
        """
        return default_token_generator.check_token(user, token)
