from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request
from django.db.models import Q
from unidecode import unidecode
from cities_light.models import City
from app.utils import cities


class EndpointView(viewsets.GenericViewSet):
    """Base class for building views"""

    def get_queryset(self):
        ...


class CitiesView(EndpointView):
    """View for listing cities"""

    authentication_classes = []
    permission_classes = []

    def list_cities(self, request: Request) -> Response:
        """
        Return a list of cities with mapped voivodeships based on the query parameter.
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
            Q(name_ascii__icontains=mapped_city_query) | Q(region__name__in=matched_voivodeships)
        )

        # Iterate over the results and create a list of city-voivodeship pairs
        cities_list = [
            [
                # Get the mapped city name from the CUSTOM_CITY_MAPPING if available, otherwise use the original city name
                cities.CUSTOM_CITY_MAPPING.get(city.name, city.name),
                # Map the voivodeship name to its corresponding Polish name for display
                cities.VOIVODESHIP_MAPPING.get(city.region.name, city.region.name)
            ]
            for city in filtered_cities
        ]

        return Response(cities_list, status=status.HTTP_200_OK)
