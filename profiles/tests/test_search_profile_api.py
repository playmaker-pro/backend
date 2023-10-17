from rest_framework.test import APIClient, APITestCase
from django.urls import reverse
from utils import testutils
from utils.factories import (
    UserFactory,
    PlayerProfileFactory,
    CoachProfileFactory,
    UserPreferencesFactory,
)
from roles import definitions


class TestProfileSearchAPI(APITestCase):
    def setUp(self):
        testutils.create_system_user()
        self.client = APIClient()
        self.profile_search_url = reverse("api:profiles:profile_search")
        self.user1 = UserFactory.create(
            declared_role=definitions.PLAYER_SHORT, first_name="Jon", last_name="Doe"
        )
        self.user2 = UserFactory.create(
            declared_role=definitions.COACH_SHORT, first_name="Jane", last_name="Doe"
        )

        self.user3 = UserFactory.create(declared_role=definitions.PLAYER_SHORT)
        PlayerProfileFactory.create(user=self.user1)
        PlayerProfileFactory.create(user=self.user3)
        CoachProfileFactory.create(user=self.user2)
        UserPreferencesFactory.create(user=self.user1)
        UserPreferencesFactory.create(user=self.user2)
        UserPreferencesFactory.create(user=self.user3)

    def test_search_valid_term(self):
        """
        Test searching for a profile using a complete and valid term.
        """
        response = self.client.get(self.profile_search_url, {"name": "JonDoe"})
        assert response.status_code == 200

        jon_doe_present = any(
            user["first_name"] == self.user1.first_name
            and user["last_name"] == self.user1.last_name
            for user in response.data["results"]
        )
        assert jon_doe_present

    def test_search_partial_term(self):
        """
        Test searching for profiles using a partial term.
        """
        response = self.client.get(self.profile_search_url, {"name": "Doe"})

        assert response.status_code == 200

        jon_doe_present = any(
            user["first_name"] == self.user1.first_name
            and user["last_name"] == self.user1.last_name
            for user in response.data["results"]
        )
        assert jon_doe_present

        jane_doe_present = any(
            user["first_name"] == self.user2.first_name
            and user["last_name"] == self.user2.last_name
            for user in response.data["results"]
        )
        assert jane_doe_present

    def test_search_non_existent_term(self):
        """
        Test searching for a profile using a term that does not match any user.
        """
        response = self.client.get(self.profile_search_url, {"name": "NonExistent"})
        assert response.status_code == 200
        assert len(response.data.get("results")) == 0

    def test_search_without_term(self):
        """
        Test searching for a profile without providing a search term.
        """
        response = self.client.get(self.profile_search_url)
        assert response.status_code == 400

    def test_case_insensitive_search(self):
        """
        Test that the search is case-insensitive.
        """
        response = self.client.get(self.profile_search_url, {"name": "jondoe"})

        assert response.status_code == 200

        jon_doe_present = any(
            user["first_name"] == self.user1.first_name
            and user["last_name"] == self.user1.last_name
            for user in response.data["results"]
        )
        assert jon_doe_present
