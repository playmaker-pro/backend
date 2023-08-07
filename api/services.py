from django.conf.global_settings import LANGUAGES
from . import errors
from .consts import *


class LocaleDataService:
    @property
    def prior_countries(self) -> list:
        """
        Get list of prior countries
        Polska, Ukraina, Słowacja, Czechy, Białoruś, Litwa
        """
        return ["PL", "UA", "SK", "CZ", "BY", "LT"]

    @property
    def prior_languages(self) -> list:
        """
        Get list of prior languages
        [Polish, German, Ukrainian, English]
        """
        return ["pl", "de", "uk", "en"]

    @property
    def prior_cities(self) -> list:
        """
        Get list of prior cities
        """
        return ["Wrocław", "Warszawa", "Kraków", "Łódź", "Poznań"]

    @property
    def available_languages(self) -> list:
        """Get all available language codes"""
        return [language[0] for language in LANGUAGES]

    def validate_language(self, language_code: str) -> None:
        """Validate language_code used for translations"""
        available_languages: list = self.available_languages
        if language_code not in available_languages:
            raise errors.InvalidLanguageCode(language_code, available_languages)

    def is_prior_country(self, country_code: str) -> bool:
        """Check if given country is priority"""
        return country_code in self.prior_countries

    def is_prior_city(self, city_name: str) -> bool:
        """Check if given city is priority"""
        return city_name in self.prior_cities

    def is_prior_language(self, language_code: str) -> bool:
        """Check if language is priority"""
        return language_code in self.prior_languages

    def get_dial_code(self, country_code: str) -> str:
        """Get country dial code with country code"""
        return COUNTRY_CODE_WITH_DIAL_CODE.get(country_code)
