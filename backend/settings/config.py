import os as _os
from enum import Enum

from pm_core.config import APIAuthorization, ServiceSettings
from pydantic import BaseSettings, Field


class BaseConfig(BaseSettings):
    """Base settings for webapp"""

    class Config:
        env_file = _os.path.join(
            _os.path.dirname(
                _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
            ),
            ".env",
        )
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        extra = "allow"
        use_enum_values = True


class ScrapperConfig(BaseConfig):
    """Settings for scrapper"""

    auth: APIAuthorization
    base_url: str = "http://localhost:8080"

    class Config(BaseConfig.Config):
        env_prefix = "SCRAPPER__"

    @property
    def scrapper_api_url(self) -> str:
        return _os.path.join(self.base_url, "api/")

    @property
    def scrapper_service(self) -> ServiceSettings:
        return ServiceSettings(address=self.scrapper_api_url, name="scrapper_service")


class TpayConfig(BaseConfig):
    """Settings for tpay"""

    class TpayCredentials(BaseConfig):
        client_id: str
        client_secret: str
        scope: str

    class CallbackConfig(BaseConfig):
        class Redirect(BaseConfig):
            success: str = Field(
                env="TPAY__CALLBACKS__REDIRECT__SUCCESS"
            )  # url to redirect user on success (FE url)
            error: str = Field(
                env="TPAY__CALLBACKS__REDIRECT__SUCCESS"
            )  # url to redirect user on error (FE url)

        class Notification(BaseConfig):
            email: str  # email address for payment notification
            url: str  # url to which tpay will send payment notification

        payerUrls: Redirect = Field(env="TPAY__CALLBACKS__REDIRECT")
        notification: Notification

    credentials: TpayCredentials
    callbacks: CallbackConfig
    security_code: str  # tpay security code (settings -> notifications -> security)
    base_url: str
    test_mode: bool


class RedisConfig(BaseConfig):
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


class DatabaseConfig(BaseConfig):
    host: str
    port: int
    db: str
    username: str = ""
    password: str = ""


class WebappConfig(BaseConfig):
    """Settings for webapp"""

    url: str = "https://playmaker.pro/"

    def parse_url(self, path: str) -> str:
        return f"{self.url}{path.lstrip('/')}"


class Config(BaseConfig):
    """General settings for webapp"""

    scrapper: ScrapperConfig
    tpay: TpayConfig
    environment: Environment
    redis: RedisConfig
    postgres: DatabaseConfig
    webapp: WebappConfig
    # add the rest of settings that should fit here
