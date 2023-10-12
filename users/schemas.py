from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


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


class UserFacebookDetailPydantic(BaseModel):
    """User details from Facebook. Data needed for registration."""

    sub: str = Field(..., alias="id")
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


class RegisterSchema(BaseModel):
    """Schema represents data which have to be used by register endpoint"""

    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    password: str


class LoginSchemaOut(BaseModel):
    """Schema represents data which have to be returned by login endpoint"""

    refresh: str
    access: str
    last_name: Optional[str]
    first_name: Optional[str]
    id: int
