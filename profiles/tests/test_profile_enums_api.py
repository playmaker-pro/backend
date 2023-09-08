from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from profiles.utils import get_past_date
from roles.definitions import CLUB_ROLES
from utils import factories
from utils.test.test_utils import UserManager


class TestProfileEnumChoicesAPI(APITestCase):
    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        user_manager: UserManager = UserManager(self.client)
        self.user = user_manager.create_superuser()
        self.headers: dict = user_manager.get_headers()
        self.club_roles_url = reverse("api:profiles:club_roles")

    def test_get_club_roles(self):
        """get club roles"""
        response = self.client.get(self.club_roles_url)

        assert response.status_code == 200
        assert response.data and len(response.data) > 0

    def test_get_club_roles_valid_response_schema(self):
        """Valid response schema of club roles endpoint"""
        response = self.client.get(self.club_roles_url)

        assert isinstance(response.data, list)
        assert len(response.data) == len(CLUB_ROLES)

    def test_get_referee_roles(self):
        """get referee roles"""
        url = reverse("api:profiles:referee_roles")
        response = self.client.get(url)

        assert response.status_code == 200
        assert response.data and len(response.data) > 0

    def test_get_players_age_range(self) -> None:
        """get players count group by age"""
        birth_date_1 = get_past_date(years=20)
        birth_date_2 = get_past_date(years=25)
        birth_date_3 = get_past_date(years=30)
        factories.PlayerProfileFactory.create_with_birth_date(birth_date_1)
        factories.PlayerProfileFactory.create_with_birth_date(birth_date_2)
        factories.PlayerProfileFactory.create_with_birth_date(birth_date_3)

        response = self.client.get(reverse("api:profiles:players_age_range"))

        assert response.status_code == 200
        assert len(response.data) == 4  # +1 caused by 'total' key
