import os as _os
from enum import Enum as _Enum

from pm_core.config import APIAuthorization as _APIAuthorization
from pm_core.config import ServiceSettings as _ScrapperServiceSettings
from pydantic import BaseSettings as _BaseSettings
from pydantic import Field as _Field


class BaseConfig(_BaseSettings):
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


class ScrapperConfig(BaseConfig):
    """Settings for scrapper"""

    auth: _APIAuthorization
    base_url: str = "http://localhost:8080"

    class Config(BaseConfig.Config):
        env_prefix = "SCRAPPER__"

    @property
    def scrapper_api_url(self) -> str:
        return _os.path.join(self.base_url, "api/")

    @property
    def scrapper_service(self) -> _ScrapperServiceSettings:
        return _ScrapperServiceSettings(
            address=self.scrapper_api_url, name="scrapper_service"
        )


class TpayConfig(BaseConfig):
    """Settings for tpay"""

    class TpayCredentials(BaseConfig):
        client_id: str
        client_secret: str
        scope: str

    class CallbackConfig(BaseConfig):
        class Redirect(BaseConfig):
            success: str  # url to redirect user on success (FE url)
            error: str  # url to redirect user on error (FE url)

        class Notification(BaseConfig):
            email: str  # email address for payment notification
            result_url: str  # url to which tpay will send payment notification

        payerUrls: Redirect = _Field(alias="redirect")
        notification: Notification

    credentials: TpayCredentials
    callbacks: CallbackConfig
    security_code: str  # tpay security code (settings -> notifications -> security)
    base_url: str
    test_mode: bool


class Config(BaseConfig):
    """General settings for webapp"""

    class Environment(str, _Enum):
        production = "production"
        staging = "staging"
        development = "development"

    scrapper: ScrapperConfig
    tpay: TpayConfig
    environment: Environment
    # TODO: add the rest of settings that should fit here


config = Config()
