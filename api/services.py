from django.conf.global_settings import LANGUAGES
from . import errors


class LocaleDataService:
    @property
    def prior_countries(self) -> list:
        """
        Get list of prior countries
        Polska, Ukraina, Słowacja, Czechy, Białoruś, Litwa
        """
        return ["PL", "UA", "SK", "CZ", "BY", "LT"]

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
