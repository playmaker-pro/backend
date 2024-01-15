import os as _os

from pm_core.config import APIAuthorization as _APIAuthorization
from pm_core.config import ServiceSettings as _ScrapperServiceSettings
from pydantic import BaseSettings as _BaseSettings

from backend.settings.base import BASE_DIR


class BaseConfig(_BaseSettings):
    """Base settings for webapp"""

    class Config:
        env_file = _os.path.join(BASE_DIR, ".env")
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


class Config(BaseConfig):
    """General settings for webapp"""

    scrapper: ScrapperConfig
    # TODO: add the rest of settings that should fit here


config = Config()
