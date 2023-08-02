from rest_framework.test import APITestCase
from clubs.api.views import LeagueAPI
from utils import factories
from django.urls import reverse
from utils.testutils import create_system_user

methods = factories.MethodsSet(GET="get_highest_parents")
request = factories.RequestFactory(LeagueAPI, methods)


class TestLeagueAPI(APITestCase):
    def setUp(self) -> None:
        create_system_user()

    def test_get_highest_parents_authenticated(self) -> None:
        """Test GET the highest parent leagues with valid authentication"""
        viewset: str = "api:clubs:highest_parent_leagues"
        factories.LeagueFactory.create_league_as_highest_parent()

        response = request.get(reverse(viewset))
        assert response.status_code == 200
        assert isinstance(response.data, list) and len(response.data) == 1

    def test_get_highest_parents_not_authenticated(self) -> None:
        """Test GET the highest parent leagues without authentication"""
        viewset: str = "api:clubs:highest_parent_leagues"

        factories.LeagueFactory.create_league_as_highest_parent()

        response = request.get(reverse(viewset), force_authentication=False)
        assert response.status_code == 401
