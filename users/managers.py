import logging
import traceback
from dataclasses import dataclass
from datetime import datetime as dt
from datetime import timedelta
from typing import Dict, Any, Tuple, TYPE_CHECKING, Union

import jwt
import requests
from allauth.socialaccount.models import SocialApp
from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.core.exceptions import ImproperlyConfigured
from django.db.models import QuerySet
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
import google_auth_oauthlib.flow
from requests import Response

if TYPE_CHECKING:
    from google_auth_oauthlib.flow import Flow


logger = logging.getLogger("django")


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


@dataclass
class GoogleSdkLoginCredentials:
    client_id: str
    client_secret: str
    project_id: str


@dataclass
class GoogleAccessToken:
    id_token: str
    access_token: str

    def decode_id_token(self) -> Dict[str, Any]:
        id_token = self.id_token
        decoded_token = jwt.decode(jwt=id_token, options={"verify_signature": False})
        return decoded_token


class GoogleManager:
    """Google manager for Google OAuth2 SDK."""

    API_URI = reverse_lazy("api:users:google-oauth2-sdk-callback")
    GOOGLE_CLIENT_TYPE = "web"
    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
    GOOGLE_ACCESS_TOKEN_OBTAIN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

    SCOPES = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid",
    ]
    # Add auth_provider_x509_cert_url if you want verification on JWTS such as ID tokens
    GOOGLE_AUTH_PROVIDER_CERT_URL = ""

    def __init__(self):
        self._credentials = self.google_sdk_login_get_credentials()

    @staticmethod
    def google_sdk_login_get_credentials() -> GoogleSdkLoginCredentials:
        """Get Google credentials from DB and settings."""
        google_qry: QuerySet = SocialApp.objects.filter(provider="google")

        if not google_qry.exists:
            msg = "Google provider is missing in DB."
            logger.critical(msg)
            raise ImproperlyConfigured(msg)

        google: SocialApp = google_qry.first()
        client_id: str = google.client_id
        client_secret: str = google.secret
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

    def _get_redirect_uri(self) -> str:
        """Get redirect URI for Google OAuth2 SDK. Needed for backend flow."""
        domain = settings.GOOGLE_REDIRECT_DOMAIN
        api_uri = self.API_URI
        redirect_uri = f"{domain}{api_uri}"
        return redirect_uri

    def _generate_client_config(self) -> dict:
        """
        Generate client config for Google OAuth2 SDK. This follows the structure
        of the official "client_secret.json" file.
        """
        client_config = {
            self.GOOGLE_CLIENT_TYPE: {
                "client_id": self._credentials.client_id,
                "project_id": self._credentials.project_id,
                "auth_uri": self.GOOGLE_AUTH_URL,
                "token_uri": self.GOOGLE_ACCESS_TOKEN_OBTAIN_URL,
                "auth_provider_x509_cert_url": self.GOOGLE_AUTH_PROVIDER_CERT_URL,
                "client_secret": self._credentials.client_secret,
                "redirect_uris": [self._get_redirect_uri()],
                "javascript_origins": [],
            }
        }
        return client_config

    def get_authorization_url(self) -> Tuple[str, str]:
        """
        Get authorization URL for Google OAuth2 SDK. Needed for backend flow.
        Reference:
        https://developers.google.com/identity/protocols/oauth2/web-server#creatingclient
        """
        redirect_uri: str = self._get_redirect_uri()
        client_config: dict = self._generate_client_config()

        google_oauth_flow: Flow = google_auth_oauthlib.flow.Flow.from_client_config(
            client_config=client_config, scopes=self.SCOPES
        )
        google_oauth_flow.redirect_uri = redirect_uri

        authorization_url, state = google_oauth_flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="select_account",
        )
        return authorization_url, state

    def get_tokens(self, *, code: str, state: str) -> "GoogleAccessToken":
        """
        Get tokens from Google OAuth2 SDK. Depends on the flow, it could be used in backend or FE side.
        """
        redirect_uri: str = self._get_redirect_uri()
        client_config: dict = self._generate_client_config()

        flow: Flow = google_auth_oauthlib.flow.Flow.from_client_config(
            client_config=client_config, scopes=self.SCOPES, state=state
        )
        flow.redirect_uri = redirect_uri
        access_credentials_payload = flow.fetch_token(code=code)

        if not access_credentials_payload:
            raise ValueError

        google_tokens = GoogleAccessToken(
            id_token=access_credentials_payload["id_token"],
            access_token=access_credentials_payload["access_token"],
        )

        return google_tokens

    def get_user_info(self, *, google_tokens: Union[GoogleAccessToken, str]):
        """
        Returns user info from Google.
        Depends on the flow, it could be used in backend or FE side.
        Reference:
        https://developers.google.com/identity/protocols/oauth2/web-server#callinganapi
        # TODO change google tokens when FLOW will be chosen
        """
        access_token = google_tokens

        if isinstance(google_tokens, GoogleAccessToken):
            access_token: str = google_tokens.access_token

        response: Response = requests.get(
            self.GOOGLE_USER_INFO_URL, params={"access_token": access_token}
        )

        if not response.ok:
            raise ValueError("Failed to obtain user info from Google.")

        return response.json()
