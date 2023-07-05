from rest_framework import viewsets
from django_countries import countries
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request
from django.utils import translation


class EndpointView(viewsets.GenericViewSet):
    """Base class for building views"""

    def get_queryset(self):
        ...


class CountriesView(EndpointView):
    """View for listing countries"""

    authentication_classes = []
    permission_classes = []
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

    def list_countries(self, request: Request) -> Response:
        """
        Return list of countries and mark prior among them
        [{"country": "Polska", "priority": True}, {"country": "Angola", "priority": False}, ...]
        It is possible to select language of countries on output by param, Polish by default
        All language codes (ISO 639-1): https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
        """
        language = request.GET.get("language", "pl")  # default language (pl -> Polish)
        translation.activate(language)
        countries_list = [
            {"country": country_name, "priority": self.is_prior_country(country_core)}
            for country_core, country_name in countries
        ]
        return Response(countries_list, status=status.HTTP_200_OK)
