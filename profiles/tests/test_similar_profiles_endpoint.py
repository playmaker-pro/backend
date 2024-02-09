from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from utils import factories

url = "api:profiles:get_similar_profiles"


class TestSimilarProfilesAPI(APITestCase):
    def setUp(self) -> None:
        """Set up objects for testing."""
        self.client: APIClient = APIClient()
        self.user = factories.UserFactory.create()
        self.client.force_authenticate(user=self.user)
        self.main_coach_role = "IC"
        self.other_coach_role = "GKC"
        self.cam_position = factories.PlayerPositionFactory.create(name="CAM")
        self.forward_position = factories.PlayerPositionFactory.create(name="Forward")

        # Create a target coach profile
        self.target_coach = factories.CoachProfileFactory.create(
            user__userpreferences__gender="M", coach_role=self.main_coach_role
        )
        self.women_coach = factories.CoachProfileFactory.create(
            user__userpreferences__gender="K", coach_role=self.main_coach_role
        )

        # Create a target player with the CAM position as the main position
        self.target_player = factories.PlayerProfileFactory.create(
            user__userpreferences__gender="M",
        )
        factories.PlayerProfilePositionFactory.create(
            player_profile=self.target_player,
            player_position=self.cam_position,
            is_main=True,
        )

    def test_get_similar_player_profiles(self) -> None:
        """
        Test retrieving similar profiles for a player profile with the same position.
        """
        # Create player profiles with the same main position (CAM)
        for _ in range(10):
            player = factories.PlayerProfileFactory.create(
                user__userpreferences__gender="M",
            )
            factories.PlayerProfilePositionFactory.create(
                player_profile=player, player_position=self.cam_position, is_main=True
            )

        # Create player profiles with a different main position (Forward)
        for _ in range(5):
            player = factories.PlayerProfileFactory.create(
                user__userpreferences__gender="M",
            )
            factories.PlayerProfilePositionFactory.create(
                player_profile=player,
                player_position=self.forward_position,
                is_main=True,
            )

        # Test API endpoint
        similar_profile_url = reverse(
            url,
            kwargs={"profile_uuid": self.target_player.uuid},
        )
        response = self.client.get(similar_profile_url)
        assert response.status_code == 200
        assert "results" in response.data
        assert self.target_player not in response.data["results"]
        assert len(response.data["results"]) >= 10

    def test_get_similar_coach_profiles(self) -> None:
        """
        Test retrieving similar profiles for a coach profile with the same coach role.
        """
        # Create coach profiles with the same coach role
        factories.CoachProfileFactory.create_batch(
            10, user__userpreferences__gender="M", coach_role=self.main_coach_role
        )

        # Create coach profiles with a different coach role
        factories.CoachProfileFactory.create_batch(
            5, user__userpreferences__gender="M", coach_role=self.other_coach_role
        )

        # Test API endpoint
        similar_profile_url = reverse(
            url,
            kwargs={"profile_uuid": self.target_coach.uuid},
        )
        response = self.client.get(similar_profile_url)
        assert response.status_code == 200
        assert "results" in response.data
        assert self.target_coach not in response.data["results"]
        assert len(response.data["results"]) >= 10
        assert self.women_coach not in response.data["results"]

    def test_gender_filter_relaxation(self):
        """
        Test the relaxation of gender filter when initial criteria do not yield enough results.
        """
        factories.CoachProfileFactory.create_batch(
            10, user__userpreferences__gender="M", coach_role=self.main_coach_role
        )
        similar_profile_url = reverse(
            url,
            kwargs={"profile_uuid": self.women_coach.uuid},
        )
        response = self.client.get(similar_profile_url)
        assert "results" in response.data
        assert len(response.data["results"]) >= 10
