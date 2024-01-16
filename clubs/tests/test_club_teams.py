from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, APITestCase

from clubs import api, models
from utils.factories import ClubWithHistoryFactory, GenderFactory, TeamFactory
from utils.test.test_utils import UserManager

User = get_user_model()


class TestClubAPI(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        user_manager = UserManager(self.client)
        self.user: User = user_manager.create_superuser()
        self.headers: dict = user_manager.get_headers()
        self.club_teams_endpoint = reverse("api:clubs:get_all_clubs_teams")

        GenderFactory(name="kobiety")
        male_gender = GenderFactory(name="mężczyźni")
        self.club = ClubWithHistoryFactory.create()

        # Set gender for all teams of this club
        self.club.teams.update(gender=male_gender)

        self.team = self.club.teams.first()
        self.league_history = self.team.league_history
        self.season = self.league_history.season
        self.league = self.league_history.league

    def test_get_club_teams_authenticated(self) -> None:
        """
        Test if authenticated users can retrieve club teams for a given season.
        """
        response = self.client.get(
            self.club_teams_endpoint, data={"season": self.season.name}, **self.headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data["results"], list)

    def test_filter_by_club_name(self) -> None:
        """
        Test if club teams can be filtered by club name for a given season and ensure
        that only teams marked as visible are included in the response.

        This test verifies that:
        1. The API correctly filters clubs by a specific club name and season.
        2. Within the filtered club, only teams that are marked as visible (`visible=True`)
        are returned in the response, while invisible teams (`visible=False`) are excluded.

        The test sets up one visible and one invisible team within the same club and
        checks the API response to ensure that only the visible team is included.
        """
        visible_team = TeamFactory(
            club=self.club, visible=True, league_history=self.league_history
        )
        invisible_team = TeamFactory(
            club=self.club, visible=False, league_history=self.league_history
        )
        response = self.client.get(
            self.club_teams_endpoint,
            data={"season": self.league_history.season.name, "name": self.club.name},
            **self.headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == self.club.name
        team_ids_in_response = [
            team["id"] for team in response.data["results"][0]["club_teams"]
        ]
        assert (
            visible_team.id in team_ids_in_response
        ), "Visible team should be in response"
        assert (
            invisible_team.id not in team_ids_in_response
        ), "Invisible team should not be in response"

    def test_pagination(self) -> None:
        """
        Test the pagination functionality of the club teams endpoint.
        This ensures that paginated results correctly represent the total number
        of clubs and that navigating through paginated results is accurate.
        """
        # Calculate number of clubs with histories for the season
        # This count helps us determine the expected number of results
        # when paginating through the API endpoint
        num_clubs = models.Club.objects.filter(
            teams__league_history__season__name=self.season
        ).count()

        # Request the first page
        response = self.client.get(
            self.club_teams_endpoint,
            data={"season": self.season.name, "page": 1, "page_size": 1},
            **self.headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["count"] == num_clubs

        for _ in range(num_clubs - 1):
            assert response.data["next"] is not None
            response = self.client.get(response.data["next"], **self.headers)
            assert response.status_code == status.HTTP_200_OK

        assert response.data["next"] is None

        response = self.client.get(
            self.club_teams_endpoint,
            data={"season": self.season.name, "page": 2, "page_size": 5},
            **self.headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_empty_page(self) -> None:
        """
        Test the scenario where a page number with no results is requested.
        It should return a 404 Not Found response.
        """
        response = self.client.get(
            self.club_teams_endpoint,
            data={"season": self.season.name, "page": 100},
            **self.headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_picture_url_generation_with_absolute_uri(self):
        """
        Test the picture URL generation ensuring it creates absolute URIs.
        This checks if the serializer correctly constructs absolute URIs
        for club pictures.
        """
        # Create a mock request and add it to serializer context
        factory = APIRequestFactory()
        request = factory.get("/")
        context = {"request": request}

        # Serialize the club
        serializer = api.serializers.ClubTeamSerializer(
            instance=self.club, context=context
        )

        # Mock the build_absolute_uri method
        with patch.object(request, "build_absolute_uri") as mock_build_absolute_uri:
            # return a dummy URL to ensure it's being called correctly
            mock_build_absolute_uri.return_value = (
                "http://testserver" + self.club.picture.url
            )

            serialized_data = serializer.data

            # Check that the build_absolute_uri method was called
            # with the correct argument
            mock_build_absolute_uri.assert_called_once_with(self.club.picture.url)

            # Validate the picture_url in the serialized data
            assert mock_build_absolute_uri.call_args[0][0] == self.club.picture.url
            assert (
                serialized_data["picture_url"]
                == "http://testserver" + self.club.picture.url
            )

    def test_filter_by_male_gender(self) -> None:
        """
        Test if club teams can be filtered by MALE gender for a given season.
        Note: Only MALE teams are created in the setUp method.
        """
        response = self.client.get(
            self.club_teams_endpoint,
            data={"season": self.season.name, "gender": "M"},
            **self.headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"], "No results returned for male teams"

        # If the gender is included in the serialized data
        for team_data in response.data["results"]:
            for club_team in team_data["club_teams"]:
                gender = club_team["gender"]["name"]
                assert gender == "mężczyźni"

    def test_filter_by_female_gender(self) -> None:
        """
        Test if club teams can be filtered by FEMALE gender for a given season.
        Note: Only MALE teams are created in the setUp method, so no results
        are expected for FEMALE teams.
        """
        response = self.client.get(
            self.club_teams_endpoint,
            data={"season": self.season.name, "gender": "F"},
            **self.headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0, "Results returned for female teams"

    def test_invisible_club_excluded_from_response(self) -> None:
        """
        Test that a club marked as invisible (visible=False) is not included in the API response.

        This test verifies that when a club is set to visible=False, it does not appear in the
        response of the API, regardless of the season or any other filters applied.
        """
        # Set the club to invisible
        self.club.visible = False
        self.club.save()

        # Attempt to retrieve clubs, including the now invisible one
        response = self.client.get(
            self.club_teams_endpoint,
            data={"season": self.league_history.season.name},
            **self.headers
        )
        assert response.status_code == status.HTTP_200_OK

        # Check that the invisible club is not in the response
        assert response.data["count"] == 0, "Invisible club should not be in response"
        assert not response.data["results"], "Response should not contain any clubs"

    def test_get_club_labels(self):
        pass
