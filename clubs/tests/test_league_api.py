from unittest.mock import MagicMock, patch

from django.urls import reverse
from parameterized import parameterized
from rest_framework.test import APIClient, APITestCase

from clubs.errors import (
    BothSeasonsGivenException,
    InvalidCurrentSeasonFormatException,
    InvalidSeasonFormatException,
)
from clubs.models import League, Season
from utils import factories
from utils.test.test_utils import UserManager


class TestListLeagueHighestParentAPI(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        user_manager = UserManager(self.client)
        self.user = user_manager.create_superuser()
        self.headers: dict = user_manager.get_headers()
        factories.GenderFactory.create_batch(2)
        self.base_league: League = (
            factories.LeagueFactory.create_league_as_highest_parent()
        )
        self.url = reverse("api:clubs:highest_parent_leagues")

    def test_get_highest_parents_authenticated(self) -> None:
        """Test GET the highest parent leagues with valid authentication"""
        response = self.client.get(self.url, **self.headers)
        assert response.status_code == 200
        assert isinstance(response.data, list) and len(response.data) == 1

    @parameterized.expand([({"gender": "M"},), ({"gender": "F"},)])
    def test_get_highest_valid_param(self, query) -> None:
        """Test GET the highest parent leagues with valid param"""
        response = self.client.get(self.url, query, **self.headers)

        assert response.status_code == 200

    @parameterized.expand([({"gender": "Male"},), ({"gender": "kobiety"},)])
    def test_get_highest_invalid_param(self, query) -> None:
        """Test fail GET the highest parent leagues with invalid param"""
        response = self.client.get(self.url, query, **self.headers)

        assert response.status_code == 400

    def test_test_get_highest_not_visible(self) -> None:
        """
        Test GET the highest parent leagues
        where object is not visible (visible=False)
        """
        league: League = factories.LeagueFactory.create_league_as_highest_parent(
            visible=False
        )
        response = self.client.get(self.url, **self.headers)
        assert response.status_code == 200
        assert isinstance(response.data, list) and len(response.data) == 1
        assert response.data[0]["name"] != league.name

    def test_get_highest_parents_with_season_param(self) -> None:
        """Test GET the highest parent leagues with season param"""
        season1: Season = factories.SeasonFactory.create(name="2020/2021")
        season2: Season = factories.SeasonFactory.create(name="2021/2022")

        league: League = factories.LeagueFactory.create_league_as_highest_parent()
        league.data_seasons.add(season1)

        league2: League = factories.LeagueFactory.create_league_as_highest_parent()
        league2.data_seasons.add(season2)

        response = self.client.get(self.url, {"season": "2020/2021"}, **self.headers)
        assert response.status_code == 200
        assert isinstance(response.data, list) and len(response.data) == 1
        assert League.objects.all().count() == 3
        assert response.data[0]["id"] == league.pk

        league: League = factories.LeagueFactory.create_league_as_highest_parent()
        league.data_seasons.add(season2)

        response = self.client.get(self.url, {"season": "2021/2022"}, **self.headers)
        assert isinstance(response.data, list) and len(response.data) == 2

    @patch.object(Season, "current_season_update", MagicMock(return_value=None))
    def test_get_highest_parents_with_current_season_param(self) -> None:
        """Test GET the highest parent leagues with current season param"""

        current_season: Season = factories.SeasonFactory.create(is_current=True)
        league: League = factories.LeagueFactory.create_league_as_highest_parent()
        league.data_seasons.add(current_season)

        response = self.client.get(self.url, {"current_season": "true"}, **self.headers)

        assert response.status_code == 200
        assert isinstance(response.data, list) and len(response.data) == 1
        assert League.objects.all().count() == 2

        assert response.data[0]["id"] == league.pk
        assert response.data[0]["id"] != self.base_league.pk

    def test_both_season_and_current_season_params_given(self) -> None:
        """
        Test GET the highest parent leagues with both season and current season params.
        Expected 400 response.
        """

        response = self.client.get(
            self.url, {"current_season": "true", "season": "2020/2021"}, **self.headers
        )
        assert response.status_code == 400
        assert response.data["detail"] == BothSeasonsGivenException.default_detail

    def test_invalid_season_format(self) -> None:
        """
        Test GET the highest parent leagues with invalid season format.
        Expected 400 response.
        """

        response = self.client.get(self.url, {"season": "2020"}, **self.headers)
        assert response.status_code == 400
        assert response.data["detail"] == InvalidSeasonFormatException.default_detail

        response = self.client.get(
            self.url, {"season": "2020/2020/2020"}, **self.headers
        )
        assert response.status_code == 400
        assert response.data["detail"] == InvalidSeasonFormatException.default_detail

    def test_get_highest_parents_current_season_not_valid_param(self) -> None:
        """Test GET the highest parent leagues with current season param not valid"""
        response = self.client.get(
            self.url, {"current_season": "bad param"}, **self.headers
        )

        assert response.status_code == 400
        assert (
            response.data["detail"]
            == InvalidCurrentSeasonFormatException.default_detail
        )
