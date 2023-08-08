from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from utils.test.test_utils import UserManager


class TestProfileEnumChoicesAPI(APITestCase):
    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        user_manager: UserManager = UserManager(self.client)
        self.user = user_manager.create_superuser()
        self.headers: dict = user_manager.get_headers()

    def test_get_club_roles_valid_auth(self):
        """get club roles with authentication"""
        url = reverse("api:profiles:club_roles")
        response = self.client.get(url, **self.headers)

        assert response.status_code == 200
        assert response.data and len(response.data) > 0

    def test_get_club_roles_invalid_auth(self):
        """get club roles without authentication"""
        url = reverse("api:profiles:club_roles")
        response = self.client.get(url)

        assert response.status_code == 401

    def test_get_referee_roles_valid_auth(self):
        """get referee roles with authentication"""
        url = reverse("api:profiles:referee_roles")
        response = self.client.get(url, **self.headers)

        assert response.status_code == 200
        assert response.data and len(response.data) > 0

    def test_get_referee_roles_invalid_auth(self):
        """get referee roles without authentication"""
        url = reverse("api:profiles:referee_roles")
        response = self.client.get(url)

        assert response.status_code == 401
