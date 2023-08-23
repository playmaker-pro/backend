from django.urls import reverse
from parameterized import parameterized
from rest_framework.test import APIClient, APITestCase

from utils import factories
from utils.test.test_utils import UserManager


class TestListLeagueHighestParentAPI(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        user_manager = UserManager(self.client)
        self.user = user_manager.create_superuser()
        self.headers: dict = user_manager.get_headers()
        factories.GenderFactory.create_batch(2)
        factories.LeagueFactory.create_league_as_highest_parent()
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
