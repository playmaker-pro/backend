from functools import cached_property

from django.conf.global_settings import LANGUAGES
from django_countries.data import COUNTRIES

from . import errors
from .consts import *


class LocaleDataService:
    @cached_property
    def country_codes(self) -> list:
        """Return and cache country codes"""
        return list(COUNTRIES.keys())

    @cached_property
    def mapped_languages(self) -> dict:
        """Get language dictionary {lang_code: en_lang_name}"""
        return dict(LANGUAGES)

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

    def validate_country_code(self, code: str) -> str:
        """Validate country code. Raise exception if given code is invalid, return code otherwise"""
        code = code.upper()
        if code not in self.country_codes:
            raise ValueError(
                f"Invalid country code: '{code}'. Choices: {self.country_codes}."
            )
        return code

    def validate_language_code(self, code: str) -> str:
        """Validate language code. Raise exception if given code is invalid, return code otherwise"""
        code = code.lower()
        language_codes: list = list(self.mapped_languages.keys())
        if code not in language_codes:
            raise ValueError(
                f"Invalid language code: '{code}', choices: {language_codes}"
            )
        return code

    def get_english_language_name_by_code(self, code: str) -> str:
        """
        Get english language name by language code.
        English name is needed in order to translate name to any other language.
        """
        return self.mapped_languages.get(code)
