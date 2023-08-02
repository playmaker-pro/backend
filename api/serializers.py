from rest_framework import serializers
from utils import translate_to
import typing
from django.utils import translation


class LanguageListSerializer(serializers.ListSerializer):
    def to_internal_value(self, data: list) -> typing.List[dict]:
        """
        Pass languages as list of tuples as:
        [(language_code, language_name), ...]
        Pass language code (ISO 639-1) as context to translate language names
        Available language codes: https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes

        {
            language - name of language translated in langauge described by context param
            language_locale - name of language translated as native locale language
            code - language code
        }
        """
        language: str = self.context.get("language", "pl")
        return [
            {
                "language": translate_to(language, language_name).capitalize(),
                "language_locale": translate_to(
                    language_code, language_name
                ).capitalize(),
                "code": language_code,
            }
            for language_code, language_name in data
        ]


class LanguageSerializer(serializers.Serializer):
    language = serializers.CharField(read_only=True)
    language_locale = serializers.CharField(read_only=True)
    code = (
        serializers.CharField()
    )  # we assume that UserPreferences will save language by code

    class Meta:
        list_serializer_class = LanguageListSerializer


class CountriesListSerializer(serializers.ListSerializer):
    prior_countries = [
        "PL",
        "UA",
        "SK",
        "CZ",
        "BY",
        "LT",
    ]  # Polska, Ukraina, Słowacja, Czechy, Białoruś, Litwa

    def is_prior_country(self, country_code: str) -> bool:
        """Check if given country is priority"""
        return country_code in self.prior_countries

    def to_internal_value(self, data: list) -> typing.List[dict]:
        """
        Return list of countries and mark prior among them
        [{"country": "Polska", "priority": True}, {"country": "Angola", "priority": False}, ...]
        Select language of countries on output by param (e.g. ?language=en, Default: pl - polish).
        All language codes (ISO 639-1): https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
        """
        language: str = self.context.get("language", "pl")
        translation.activate(language)
        return [
            {
                "country": country_name,
                "code": country_code,
                "priority": self.is_prior_country(country_code),
            }
            for country_code, country_name in data
        ]


class CountrySerializer(serializers.Serializer):
    country = serializers.CharField(read_only=True)
    code = (
        serializers.CharField()
    )  # we assume that UserPreferences will save country by code
    priority = serializers.BooleanField(read_only=True)

    class Meta:
        list_serializer_class = CountriesListSerializer
