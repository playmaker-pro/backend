from rest_framework import serializers
from .services import LocaleDataService
from utils import translate_to
import typing
from django.utils import translation
from cities_light.models import City
from app.utils import cities

locale_service = LocaleDataService()


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
        locale_service.validate_language(language)
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
    priority = serializers.SerializerMethodField()

    class Meta:
        list_serializer_class = LanguageListSerializer

    def get_priority(self, obj) -> bool:
        """Define language priority"""
        return locale_service.is_prior_language(obj["code"])


class CountriesListSerializer(serializers.ListSerializer):
    def to_internal_value(self, data: list) -> typing.List[dict]:
        """
        Return list of countries and mark prior among them
        [{"country": "Polska", "priority": True}, {"country": "Angola", "priority": False}, ...]
        Select language of countries on output by param (e.g. ?language=en, Default: pl - polish).
        All language codes (ISO 639-1): https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
        """
        language: str = self.context.get("language", "pl")
        locale_service.validate_language(language)
        translation.activate(language)
        return [
            {
                "country": country_name,
                "code": country_code,
            }
            for country_code, country_name in data
        ]


class CountrySerializer(serializers.Serializer):
    country = serializers.CharField(read_only=True)
    code = (
        serializers.CharField()
    )  # we assume that UserPreferences will save country by code
    priority = serializers.SerializerMethodField()
    dial_code = serializers.SerializerMethodField()

    class Meta:
        list_serializer_class = CountriesListSerializer

    def get_priority(self, obj: dict) -> bool:
        """Define country priority"""
        return locale_service.is_prior_country(obj["code"])

    def get_dial_code(self, obj: dict) -> str:
        """Define country dial code"""
        return locale_service.get_dial_code(obj["code"])


class CitySerializer(serializers.ModelSerializer):
    voivodeship = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = City
        fields = ("id", "name", "voivodeship", "priority")

    def get_voivodeship(self, obj: City) -> str:
        """Transform voivodeship name"""
        region = obj.region.name
        return cities.VOIVODESHIP_MAPPING.get(region, region)

    def get_name(self, obj: City) -> str:
        """Transform city name"""
        return cities.CUSTOM_CITY_MAPPING.get(obj.name, obj.name)

    def get_priority(self, obj: City) -> bool:
        """define city priority"""
        city_name = cities.CUSTOM_CITY_MAPPING.get(obj.name, obj.name)
        return locale_service.is_prior_city(city_name)
