from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request
from django.db.models import Q
from unidecode import unidecode
from cities_light.models import City


class EndpointView(viewsets.GenericViewSet):
    """Base class for building views"""

    def get_queryset(self):
        ...


class CityQueryView(EndpointView):
    """View for querying cities"""

    authentication_classes = []
    permission_classes = []

    VOIVODESHIP_MAPPING = {
        "Silesia": "Śląskie",
        "Mazovia": "Mazowieckie",
        "Lesser Poland": "Małopolskie",
        "Podlasie": "Podlaskie",
        "Warmia-Masuria": "Warmińsko-mazurskie",
        "Lower Silesia": "Dolnośląskie",
        "Łódź Voivodeship": "Łódzkie",
        "Lubusz": "Lubuskie",
        "Opole Voivodeship": "Opolskie",
        "Pomerania": "Pomorskie",
        "Greater Poland": "Wielkopolskie",
        "West Pomerania": "Zachodniopomorskie",
        "Lublin": "Lubelskie",
        "Świętokrzyskie": "Świętokrzyskie",
        "Subcarpathia": "Podkarpackie",
        "Kujawsko-Pomorskie": "Kujawsko-Pomorskie"
    }

    CUSTOM_CITY_MAPPING = {
        "Warsaw": "Warszawa",

    }

    def map_voivodeship(self, voivodeship_name: str) -> str:
        """
        Maps the voivodeship name to a standardized form.
        The voivodeship names in the `City` model of the `django-cities-light` library are stored in English.
        However, the queries for voivodeships are expected to be in Polish. This method maps the Polish voivodeship
        names to their standardized English form for consistent comparison.
        """
        return self.VOIVODESHIP_MAPPING.get(voivodeship_name, voivodeship_name)

    def match_voivodeship(self, query: str) -> list:
        """
        Matches the query to a list of voivodeships.

        The method compares the lowercase, unidecoded query with the lowercase, unidecoded voivodeship names
        stored in the `VOIVODESHIP_MAPPING` dictionary. This allows the query to be immune to Polish language
        letters and case sensitivity. If the query partially matches a voivodeship name, it is added to the
        list of matched queries.
        """
        matched_queries = []

        for key, value in self.VOIVODESHIP_MAPPING.items():
            if query.lower() in unidecode(value.lower()):
                matched_queries.append(key)
        return matched_queries

    def handle_custom_city_mapping(self, query: str) -> str:
        """
        Handles the custom city mappings where the name_ascii field in django-cities-light does not match the Polish city names.
        If a match is found, the decoded_query is updated with the corresponding key from the CUSTOM_CITY_MAPPING.
        """
        for key, value in self.CUSTOM_CITY_MAPPING.items():
            if query.lower() in unidecode(value.lower()):
                query = key
        return query

    def list_cities(self, request: Request) -> Response:
        """
        Return a list of cities with mapped voivodeships based on the query parameter.
        """
        # Get the value of the "city" query parameter
        query = request.GET.get("city", "")

        # Remove Polish language letters from the query
        decoded_query = unidecode(query)

        # Match the query to a list of voivodeships
        matched_voivodeships = self.match_voivodeship(decoded_query)

        # Check if the query matches any custom mappings
        # This handles the case where the name_ascii field in django-cities-light does not match the Polish city names.
        # For example, "Warszawa" is stored as "Warsaw" in the name_ascii field.
        # If a match is found, the decoded_query is updated with the corresponding key from the CUSTOM_CITY_MAPPING.
        cities_query = self.handle_custom_city_mapping(decoded_query)

        # Filter cities based on the decoded query (matching city names) or matched voivodeships
        filtered_cities = City.objects.filter(
            Q(name_ascii__icontains=cities_query) | Q(region__name__in=matched_voivodeships)
        )

        # Iterate over the results and create a list of city-voivodeship pairs
        cities_list = [
            [
                city.name,
                self.map_voivodeship(city.region.name)
            ]
            for city in filtered_cities
        ]

        return Response(cities_list, status=status.HTTP_200_OK)
