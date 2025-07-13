import os as _os
from enum import Enum

from pm_core.config import APIAuthorization, ServiceSettings
from pydantic import BaseModel, BaseSettings, Field


class ScrapperConfig(BaseModel):
    """Settings for scrapper"""

    auth: APIAuthorization
    base_url: str = "http://localhost:8080"

    @property
    def scrapper_api_url(self) -> str:
        return _os.path.join(self.base_url, "api/")

    @property
    def scrapper_service(self) -> ServiceSettings:
        return ServiceSettings(address=self.scrapper_api_url, name="scrapper_service")


class TpayConfig(BaseModel):
    """Settings for tpay"""

    class TpayCredentials(BaseModel):
        client_id: str
        client_secret: str
        scope: str

    class CallbackConfig(BaseModel):
        class Redirect(BaseModel):
            success: str
            error: str

        class Notification(BaseModel):
            email: str  # email address for payment notification
            url: str  # url to which tpay will send payment notification

        payerUrls: Redirect = Field(alias="redirect")
        notification: Notification

    credentials: TpayCredentials
    callbacks: CallbackConfig
    security_code: str  # tpay security code (settings -> notifications -> security)
    base_url: str
    test_mode: bool


class RedisConfig(BaseModel):
    host: str
    port: int
    db: int
    password: str
    username: str

    @property
    def url(self) -> str:
        auth = f"{self.username}:{self.password}@" if self.username else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class Environment(Enum):
    PRODUCTION = "production"
    STAGING = "staging"
    DEV = "development"
    TEST = "test"


class DatabaseConfig(BaseModel):
    host: str
    port: int
    db: str
    user: str = ""
    password: str = ""


class WebappConfig(BaseModel):
    """Settings for webapp"""

    url: str = "https://playmaker.pro/"

    def parse_url(self, path: str) -> str:
        return f"{self.url}{path.lstrip('/')}"


class SocialAuthConfig(BaseModel):
    """Settings for social authentication"""

    class FacebookConfig(BaseModel):
        app_secret: str

    facebook: FacebookConfig


class AppConfiguration(BaseSettings):
    """General settings for webapp"""

    scrapper: ScrapperConfig
    tpay: TpayConfig
    environment: Environment
    redis: RedisConfig
    postgres: DatabaseConfig
    webapp: WebappConfig
    social: SocialAuthConfig
    # add the rest of settings that should fit here

    class Config:
        env_file = _os.path.join(
            _os.path.dirname(
                _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
            ),
            ".env",
        )
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        use_enum_values = True
        nested_model_default_partial_update = True


app_config = AppConfiguration()
