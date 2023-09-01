from django.urls import reverse
from parameterized import parameterized
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from clubs.services import ClubTeamService
import pytest

from utils.factories import (
    ClubFactory,
    GenderFactory,
    SeasonFactory,
    TeamFactory,
    consts,
)
from utils.test.test_utils import UserManager
from django.contrib.auth import get_user_model

User = get_user_model()


class TestClubTeamsAPI(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        user_manager = UserManager(self.client)
        self.user: User = user_manager.create_superuser()
        self.headers: dict = user_manager.get_headers()
        self.club_teams_endpoint = reverse("api:clubs:club_teams")
        self.club = ClubFactory.create()
        self.team = TeamFactory(club=self.club)
        self.season = SeasonFactory()
        GenderFactory.create_batch(2)

    def test_get_club_teams_authenticated(self) -> None:
        """Test GET the club teams with valid authentication"""
        response = self.client.get(
            self.club_teams_endpoint, data={"season": self.season}, **self.headers
        )

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data["clubs"], list)

    @parameterized.expand(
        [
            *[
                (club_name, "2023/2024", "M", status.HTTP_200_OK)
                for club_name in consts.CLUB_NAMES
            ],
            *[
                (club_name, season_name, "M", status.HTTP_200_OK)
                for club_name in consts.CLUB_NAMES
                for season_name in consts.SEASON_NAMES
            ],
            *[
                (club_name, "2023/2024", gender, status.HTTP_200_OK)
                for club_name in consts.CLUB_NAMES
                for gender in ["M", "F"]
            ],
            ("NonExistentClub", "2023/2024", "M", status.HTTP_200_OK),
            ("SomeValidClub", "InvalidSeason", "M", status.HTTP_200_OK),
            ("SomeValidClub", "2023/2024", "Z", status.HTTP_400_BAD_REQUEST),
        ]
    )
    def test_get_club_teams_with_parameters(
        self, club_name, season_name, gender, expected_status
    ) -> None:
        """Test GET the club teams with query parameters"""
        query_params = {"name": club_name, "season": season_name, "gender": gender}

        response = self.client.get(
            self.club_teams_endpoint, query_params, **self.headers
        )
        assert response.status_code == expected_status
