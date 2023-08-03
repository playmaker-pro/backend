from rest_framework import viewsets
from django_countries import countries
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request
from django.db.models import Q
from unidecode import unidecode
from cities_light.models import City
from app.utils import cities
from users.models import UserPreferences
from profiles.models import PlayerProfile
from drf_yasg.utils import swagger_auto_schema
from api.swagger_schemas import (
    CITIES_VIEW_SWAGGER_SCHEMA,
    PREFERENCE_CHOICES_VIEW_SWAGGER_SCHEMA,
)
from django.conf.global_settings import LANGUAGES
from . import serializers


class EndpointView(viewsets.GenericViewSet):
    """Base class for building views"""

    def get_queryset(self):
        ...


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
        serializer = serializers.CountrySerializer(
            data=countries, many=True, context={"language": language}
        )
        serializer.is_valid()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(**CITIES_VIEW_SWAGGER_SCHEMA)
    def list_cities(self, request: Request) -> Response:
        """
        Return a list of cities with mapped voivodeships based on the query parameter.
        Each item in the response array is a pair of strings:
        [city name, voivodeship name].
        For example: ["Aleksandrów Łódzki", "Łódzkie"].
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
        filtered_cities = City.objects.filter(
            Q(name_ascii__icontains=mapped_city_query)
            | Q(region__name__in=matched_voivodeships)
        )

        # Iterate over the results and create a list of city-voivodeship pairs
        cities_list = [
            [
                # Get the mapped city name from the CUSTOM_CITY_MAPPING if available, otherwise use the original city name
                cities.CUSTOM_CITY_MAPPING.get(city.name, city.name),
                # Map the voivodeship name to its corresponding Polish name for display
                cities.VOIVODESHIP_MAPPING.get(city.region.name, city.region.name),
            ]
            for city in filtered_cities
        ]

        return Response(cities_list, status=status.HTTP_200_OK)

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
        serializer = serializers.LanguageSerializer(
            data=LANGUAGES, many=True, context={"language": language}
        )
        serializer.is_valid()
        return Response(serializer.data, status=status.HTTP_200_OK)


class PreferenceChoicesView(EndpointView):
    """View for listing gender and preferred leg choices"""

    authentication_classes = []
    permission_classes = []

    @swagger_auto_schema(**PREFERENCE_CHOICES_VIEW_SWAGGER_SCHEMA)
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
