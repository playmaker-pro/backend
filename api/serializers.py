import typing
from functools import cached_property

from cities_light.models import City
from django.utils import translation
from django_countries import CountryTuple
from rest_framework import serializers

from app.utils import cities
from users.models import UserPreferences

from .services import LocaleDataService

locale_service = LocaleDataService()


class CountrySerializer(serializers.Serializer):
    country = serializers.SerializerMethodField(read_only=True)
    code = (
        serializers.CharField()
    )  # we assume that UserPreferences will save country by code
    priority = serializers.SerializerMethodField()
    dial_code = serializers.SerializerMethodField()

    _CHOICES = UserPreferences.COUNTRIES

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        language = self.context.get("language", "pl")
        try:
            locale_service.validate_language_code(language)
        except ValueError as e:
            raise serializers.ValidationError(e)
        translation.activate(language)

    @cached_property
    def set_to_dict(self) -> dict:
        """Create dictionary out of countries tuple"""
        return dict(self._CHOICES)

    def to_representation(self, obj: typing.Union[CountryTuple, str]) -> dict:
        """Create CountryTuple if country is passed as string (e.g. as saved in UserPreferences)"""
        if isinstance(obj, str):
            obj = CountryTuple(obj, self.set_to_dict[obj])
        return super().to_representation(obj)

    def get_country(self, obj: CountryTuple) -> str:
        """Get country name"""
        return obj.name

    def get_priority(self, obj: CountryTuple) -> bool:
        """Define country priority"""
        return locale_service.is_prior_country(obj.code)

    def get_dial_code(self, obj: CountryTuple) -> str:
        """Define country dial code"""
        return locale_service.get_dial_code(obj.code)


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

    def to_internal_value(self, data: dict) -> typing.Union[City, dict]:
        """Override method to retrieve object by id"""
        if isinstance(data, int):
            return City.objects.get(id=data)
        return data
