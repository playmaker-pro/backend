import logging
import traceback
from dataclasses import dataclass
from datetime import datetime as dt
from datetime import timedelta
from typing import Optional

import requests
from allauth.socialaccount.models import SocialApp
from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from pydantic import ValidationError
from requests import Response

from users.entities import (GoogleSdkLoginCredentials, SocialAppPydantic,
                            UserGoogleDetailPydantic)

logger = logging.getLogger("django")


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
        user = self.model(email=email, username=email, **extra_fields)
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


class GoogleManager:
    """Google manager for Google OAuth2 SDK."""

    GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

    def __init__(self):
        self._credentials = self.google_sdk_login_get_credentials()

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

    def get_user_info(self, access_token: str) -> UserGoogleDetailPydantic:
        """
        Returns user info from Google as UserGoogleDetailPydantic instance.
        Example response from google:
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
        response: Response = requests.get(
            self.GOOGLE_USER_INFO_URL, params={"access_token": access_token}
        )

        if not response.ok:
            error: str = response.json().get("error")
            error_description: str = response.json().get("error_description")
            raise ValueError(f"{error}. Reason: {error_description}")

        try:
            details: UserGoogleDetailPydantic = UserGoogleDetailPydantic(
                **response.json()
            )
            return details
        except ValidationError as e:
            logger.critical(str(traceback.format_exc()) + f"\n{e}")
            raise ValueError(e)
