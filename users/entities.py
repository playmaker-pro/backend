from typing import Optional

from pydantic import BaseModel


class SocialAppPydantic(BaseModel):
    client_id: Optional[str]
    client_secret: Optional[str]


class UserGoogleDetailPydantic(BaseModel):
    sub: Optional[str]
    given_name: str
    family_name: str
    email: str


class GoogleSdkLoginCredentials(BaseModel):
    client_id: str
    client_secret: str
    project_id: str
