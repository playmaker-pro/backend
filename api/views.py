from cities_light.models import City
from django.db.models import QuerySet
from django_countries import countries
from drf_spectacular.utils import extend_schema
from rest_framework import exceptions, serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from unidecode import unidecode

from api.base_view import EndpointView
from app.utils import cities
from profiles.api.serializers import LanguageSerializer
from profiles.models import Language, PlayerProfile
from users.models import UserPreferences
from . import errors
from . import serializers as api_serializers
from .services import LocaleDataService

locale_service: LocaleDataService = LocaleDataService()




class LocaleDataView(EndpointView):
    """Viewset for listing locale data"""

    authentication_classes = []
    permission_classes = []

    def list_countries(self, request: Request) -> Response:
        """
        Return list of countries and mark prior among them
        [{"country": "Polska", "priority": True}, {"country": "Angola", "priority": False}, ...]
        Select language of countries on output by param (e.g. ?language=en, Default: pl - polish).
        All language codes (ISO 639-1): https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
        """
        language = request.GET.get("language", "pl")

        try:
            serializer = api_serializers.CountrySerializer(
                data=countries, many=True, context={"language": language}
            )
        except serializers.ValidationError as e:
            raise errors.InvalidLanguageCode(e.detail)

        serializer.is_valid()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def list_cities(self, request: Request) -> Response:
        """
        Return a list of cities with mapped voivodeships
        and its priority based on the query parameter.
        Response is an array of dictionaries:
        [{id: 1, name: Warszawa, voivodeship: Mazowieckie, priority: True}, ...]
        """
        # Get the value of the "city" query parameter
        city_query = request.GET.get("city", "")

        # Remove Polish language letters from the city query
        decoded_city_query = unidecode(city_query)

        # Match the query to a list of voivodeships
        matched_voivodeships = cities.match_voivodeship(decoded_city_query)

        # Check if the query matches any custom mappings
        # This handles the case where the name_ascii field in django-cities-light does not match the Polish city names.
        # For example, "Warszawa" is stored as "Warsaw" in the name_ascii field.
        # If a match is found, the decoded_query is updated with the corresponding key from the CUSTOM_CITY_MAPPING.
        mapped_city_query = cities.handle_custom_city_mapping(decoded_city_query)

        # Filter cities based on the decoded query (matching city names) or matched voivodeships
        # If request has no param, return just prior countries
        if not city_query:
            cities_qs: QuerySet = locale_service.get_prior_cities_queryset()
        else:
            cities_qs: QuerySet = locale_service.get_cities_queryset_by_query_param(
                city_like=mapped_city_query, voivo_like=matched_voivodeships
            )

        cities_qs: QuerySet = self.get_paginated_queryset(cities_qs)
        serializer = api_serializers.CitySerializer(cities_qs, many=True)
        return self.get_paginated_response(serializer.data)

    def list_languages(self, request: Request) -> Response:
        """
        Return list of languages.
        View takes one optional param: ?language=<lang_code> (Default: pl - polish)
        All language codes (ISO 639-1): https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes

        {
            language - name of language translated in langauge described by param
            language_locale - name of language translated as native locale language
            code - language code
        }
        """
        language = request.GET.get("language", "pl")
        qs = Language.objects.all()
        serializer = LanguageSerializer(qs, many=True, context={"language": language})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_my_city(self, request: Request) -> Response:
        """Get the closest city based on coordinates supplied in query params"""
        latitude, longitude = (
            request.query_params.get("latitude"),
            request.query_params.get("longitude"),
        )

        if not latitude or not longitude:
            raise errors.ParamsRequired(("latitude", "longitude"))

        try:
            city: City = locale_service.get_closest_city(latitude, longitude)
        except ValueError as e:
            raise exceptions.ValidationError(str(e))

        serializer = api_serializers.CitySerializer(city)

        return Response(serializer.data)


class PreferenceChoicesView(EndpointView):
    """View for listing gender and preferred leg choices"""
    from api.swagger_schemas import PREFERENCE_CHOICES_VIEW_SWAGGER_SCHEMA

    authentication_classes = []
    permission_classes = []

    @extend_schema(**PREFERENCE_CHOICES_VIEW_SWAGGER_SCHEMA)
    def list_preference_choices(self, request: Request) -> Response:
        """
        Retrieve the choices for gender and preferred leg fields and return as a response
        """

        gender_choices = [
            {"value": choice[0], "label": choice[1]}
            for choice in UserPreferences.GENDER_CHOICES
        ]
        leg_choices = [
            {"value": choice[0], "label": choice[1]}
            for choice in PlayerProfile.LEG_CHOICES
        ]
        preference_choices = {
            "gender": gender_choices,
            "player_preferred_leg": leg_choices,
        }
        return Response(preference_choices, status=status.HTTP_200_OK)
