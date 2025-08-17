import typing
from functools import cached_property

from cities_light.models import City
from django.db.models import Model
from django.utils import translation
from django_countries import CountryTuple
from rest_framework import serializers as _serializers
from rest_framework.fields import empty

from api.consts import ChoicesTuple
from api.errors import (
    ChoiceFieldValueErrorException,
    ChoiceFieldValueErrorHTTPException,
    PhoneNumberMustBeADictionaryHTTPException,
)
from api.i18n import I18nSerializerMixin
from api.services import LocaleDataService
from app.utils import cities
from users.errors import CityDoesNotExistException, CityDoesNotExistHTTPException
from users.models import UserPreferences
from users.services import UserPreferencesService

locale_service = LocaleDataService()


class CountrySerializer(_serializers.Serializer):
    country = _serializers.SerializerMethodField(read_only=True)
    code = _serializers.CharField()
    priority = _serializers.SerializerMethodField(read_only=True)
    dial_code = _serializers.SerializerMethodField(read_only=True)

    _CHOICES = UserPreferences.COUNTRIES

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        language = self.context.get("language", "pl")
        try:
            locale_service.validate_language_code(language)
        except ValueError as e:
            raise _serializers.ValidationError(e)
        translation.activate(language)

    def run_validation(self, *args) -> str:
        """Override method to retrieve object by id"""
        return args[0]

    @cached_property
    def set_to_dict(self) -> dict:
        """Create dictionary out of countries tuple"""
        return dict(self._CHOICES)

    def to_representation(self, obj: typing.Union[CountryTuple, str]) -> dict:
        """Create CountryTuple if country is passed as string (e.g. as saved in UserPreferences)"""  # noqa: 501
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


class CitySerializer(_serializers.ModelSerializer):
    voivodeship = _serializers.SerializerMethodField()
    priority = _serializers.SerializerMethodField()
    name = _serializers.SerializerMethodField()

    class Meta:
        model = City
        fields = (
            "id",
            "name",
            "voivodeship",
            "priority",
            "latitude",
            "longitude",
        )

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
            user_preferences_service: UserPreferencesService = UserPreferencesService()
            try:
                city: City = user_preferences_service.get_city_by_id(data)
                return city
            except CityDoesNotExistException:
                raise CityDoesNotExistHTTPException
        return data


class ProfileEnumChoicesSerializer(I18nSerializerMixin, _serializers.CharField, _serializers.Serializer):
    """Serializer for Profile Enums with translation support"""

    def __init__(
        self,
        model: typing.Union[
            typing.Type[Model], typing.Generator, typing.List[ChoicesTuple]
        ] = None,
        raise_exception: bool = True,
        *args,
        **kwargs,
    ):
        self.raise_exception = raise_exception
        self.model: typing.Type[Model] = model
        super().__init__(*args, **kwargs)

    def parse_dict(
        self, data: (typing.Union[int, str], typing.Union[int, str])
    ) -> dict:
        """Create dictionary from tuple choices with translation support"""
        from django.utils.translation import gettext as _
        
        # Language is already activated in __init__ via I18nSerializerMixin
        return {str(val[0]): _(str(val[1])) for val in data}  # Explicitly translate each value

    def to_representation(self, obj: typing.Union[ChoicesTuple, str]) -> dict:
        """Parse output with translation support"""
        from django.utils.translation import gettext as _

        parsed_obj = obj
        if not obj:
            return {}
        if not isinstance(obj, ChoicesTuple):
            parsed_obj = self.parse(obj)
        
        # Explicitly translate the name using Django's translation system
        translated_name = _(str(parsed_obj.name)) if parsed_obj.name else ""
        return {"id": parsed_obj.id, "name": translated_name}

    def parse(self, _id) -> ChoicesTuple:
        """Get choices by model field and parse output with translation"""
        _id = str(_id)
        choices = self.parse_dict(
            getattr(self.model, self.source).__dict__["field"].choices
        )
        if _id not in choices.keys():
            if not self.raise_exception:
                raise ChoiceFieldValueErrorException
            raise ChoiceFieldValueErrorHTTPException(
                field=self.source, choices=choices.keys(), model=self.model.__name__
            )

        value = choices[_id]
        return ChoicesTuple(_id, value)
    
    def to_internal_value(self, data):
        """Convert input data to internal value"""
        if isinstance(data, dict):
            # Handle dict input like {"id": "some_value"}
            return data.get("id", data)
        # Handle direct string/value input
        return data


class PhoneNumberField(_serializers.Field):
    """
    A custom field for handling phone numbers in the ManagerProfile serializer.

    This field is responsible for serializing and deserializing the phone number
    information (which includes 'dial_code' and 'agency_phone'). It handles the logic
    of combining these two separate fields into a single nested object for API
    representation, and it also processes incoming data for these fields
    in API requests.
    """

    def __init__(self, phone_field_name="phone_number", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.phone_field_name = (
            phone_field_name  # This can be 'phone_number' or 'agency_phone'
        )

    def run_validation(self, data=...):
        """Validate phone number field before creating object."""

        if data is not empty and not isinstance(data, dict):
            raise PhoneNumberMustBeADictionaryHTTPException
        return super().run_validation(data)

    def to_representation(
        self, obj: typing.Any
    ) -> typing.Optional[typing.Dict[str, str]]:
        """
        Converts the object's phone number information into a nested
        JSON object for API output.
        """
        dial_code = getattr(obj, "dial_code", None)
        phone_number = getattr(obj, self.phone_field_name, None)

        if dial_code is None and phone_number is None:
            return None

        return {
            "dial_code": f"+{dial_code}" if dial_code is not None else None,
            "number": phone_number,
        }

    def to_internal_value(self, data: dict) -> dict:
        """
        Processes the incoming data for the phone number field.
        """
        internal_value = {}
        dial_code = data.get("dial_code")
        phone_number = (
            data.get("number")
            if self.phone_field_name == "phone_number"
            else data.get("agency_phone")
        )

        if dial_code is not None:
            internal_value["dial_code"] = dial_code
        if phone_number is not None:
            internal_value[self.phone_field_name] = phone_number

        return internal_value
