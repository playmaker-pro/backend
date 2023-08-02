from enum import Enum
from typing import Optional

from pydantic import BaseModel


class SocialAppPydantic(BaseModel):
    """SocialApp data. Basically it's a django-auth SocialApp representation"""
    client_id: Optional[str]
    client_secret: Optional[str]


class UserGoogleDetailPydantic(BaseModel):
    """User details from Google. Data needed for registration."""
    sub: Optional[str]
    given_name: str
    family_name: str
    email: str


class GoogleSdkLoginCredentials(BaseModel):
    """Google SDK login credentials."""
    client_id: str
    client_secret: str
    project_id: str


class RedirectAfterGoogleLogin(str, Enum):
    """
    Enum represents place, where user should be redirected
    after login with Google.
    """
    REGISTER = "register"
    LANDING_PAGE = "landing page"
