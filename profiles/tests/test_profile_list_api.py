import random
from typing import List
from unittest import mock
from unittest.mock import MagicMock

import factory
import pytest
from django.db.models import signals
from django.test import override_settings
from django.urls import reverse
from parameterized import parameterized
from rest_framework.response import Response
from rest_framework.test import APIClient, APITestCase

from profiles.managers import ProfileManager
from profiles.models import LicenceType, PlayerProfile
from profiles.services import ProfileService
from profiles.utils import get_past_date
from utils import factories, get_current_season
from utils.factories import (
    LabelDefinitionFactory,
    LabelFactory,
    LeagueFactory,
    PlayerProfileFactory,
    TransferStatusFactory,
    UserFactory,
)
from utils.test.test_utils import UserManager

profile_service = ProfileService()
url: str = "api:profiles:create_or_list_profiles"
count_url: str = "api:profiles:filtered_profile_count"


class TestProfileListAPI(APITestCase):
    def setUp(self) -> None:
        """set up object factories"""
        self.client: APIClient = APIClient()
        self.user = UserManager(self.client)
        self.user_obj = self.user.create_superuser()
        self.headers = self.user.get_headers()
        self.url = reverse(url)
        self.count_url = reverse(count_url)

    def test_shuffle_list(self) -> None:
        """
        Test if results are correctly shuffled.
        We have to test for more than 10 profiles,
        because at the end of filtering, we are sorting it by data score value.
        Bigger sample of profiles, bigger change to pass this test.
        """
        factories.PlayerProfileFactory.create_batch(30)
        response1 = self.client.get(self.url, {"role": "P", "shuffle": True})
        response2 = self.client.get(self.url, {"role": "P", "shuffle": True})

        assert response1.data["results"] != response2.data["results"]

    @parameterized.expand([[{"role": "P"}], [{"role": "C"}], [{"role": "T"}]])
    def test_get_bulk_profiles(self, param) -> None:
        """get profiles by role param"""
        model = profile_service.get_model_by_role(param["role"])
        factory = factories.NAME_TO_FACTORY_MAPPER[model.__name__]
        factory.create()

        response = self.client.get(self.url, param)
        assert len(response.data["results"]) == 1
        assert response.status_code == 200

        count_response = self.client.get(self.count_url, param)
        assert count_response.data["count"] == 1
        assert count_response.status_code == 200

    @parameterized.expand([[{}], [{"role": "Piłkarz"}], [{"role": "p"}]])
    def test_get_bulk_profiles_invalid_param(self, param) -> None:
        """get profiles by invalid role param"""
        response = self.client.get(self.url, param, **self.headers)

        assert response.status_code == 400

        count_response = self.client.get(self.count_url, param, **self.headers)

        assert count_response.status_code == 400

    def test_get_bulk_profiles_youth_only(self) -> None:
        """get only youth player profiles"""
        youth_birth_date = get_past_date(years=20)
        factories.PlayerProfileFactory.create(
            user__userpreferences__birth_date=youth_birth_date
        )  # youth
        factories.PlayerProfileFactory.create(
            user__userpreferences__birth_date="1995-04-21"
        )  # not youth

        response = self.client.get(
            self.url, {"role": "P", "youth": "true"}, **self.headers
        )

        assert response.status_code == 200
        assert len(response.data["results"]) == 1

        count_response = self.client.get(
            self.count_url, {"role": "P", "youth": "true"}, **self.headers
        )

        assert count_response.status_code == 200
        assert count_response.data["count"] == 1

    def test_get_bulk_profiles_filter_age(self) -> None:
        """get player profiles with age between"""
        too_young_birth_year = get_past_date(years=20)
        exact_birth_year = get_past_date(years=25)
        too_old_birth_year = get_past_date(years=30)
        factories.PlayerProfileFactory.create(
            user__userpreferences__birth_date=too_young_birth_year
        )
        factories.PlayerProfileFactory.create(
            user__userpreferences__birth_date=exact_birth_year
        )
        factories.PlayerProfileFactory.create(
            user__userpreferences__birth_date=too_old_birth_year
        )

        response = self.client.get(
            self.url, {"role": "P", "min_age": "22", "max_age": "27"}, **self.headers
        )

        assert response.status_code == 200
        assert len(response.data["results"]) == 1

        count_response = self.client.get(
            self.count_url,
            {"role": "P", "min_age": "22", "max_age": "27"},
            **self.headers
        )

        assert count_response.status_code == 200
        assert count_response.data["count"] == 1

    def test_get_bulk_profiles_filter_position(self) -> None:
        """get player profiles filter by position"""
        player1 = factories.PlayerProfileFactory.create(
            player_positions__player_position__shortcut="CAM",
            player_positions__is_main=True,
        )
        player2 = factories.PlayerProfileFactory.create(
            player_positions__player_position__shortcut="GK",
            player_positions__is_main=True,
        )

        player1_position_id = player1.player_positions.first().player_position.id
        player2_position_id = player2.player_positions.first().player_position.id

        response = self.client.get(
            self.url,
            {"role": "P", "position": player1_position_id},
        )
        assert response.status_code == 200
        assert len(response.data["results"]) == 1

        response = self.client.get(
            self.url,
            {"role": "P", "position": [player1_position_id, player2_position_id]},
        )
        assert response.status_code == 200
        assert len(response.data["results"]) == 2

        count_response = self.client.get(
            self.count_url,
            {"role": "P", "position": player1_position_id},
        )
        assert count_response.status_code == 200
        assert count_response.data["count"] == 1

        count_response = self.client.get(
            self.count_url,
            {"role": "P", "position": [player1_position_id, player2_position_id]},
        )
        assert count_response.status_code == 200
        assert count_response.data["count"] == 2

    def test_get_bulk_profiles_filter_league(self) -> None:
        """get player profiles filter by league"""
        current_season = get_current_season()
        th1, th2 = factories.TeamFactory.create_batch(
            2, league_history__season__name=current_season
        )
        profile1 = factories.PlayerProfileFactory.create(team_object=th1)
        profile2 = factories.PlayerProfileFactory.create(team_object=th2)
        league1_id = profile1.team_object.league_history.league.id
        league2_id = profile2.team_object.league_history.league.id
        response = self.client.get(
            self.url,
            {"role": "P", "league": [league1_id]},
        )
        assert response.status_code == 200
        assert len(response.data["results"]) == 1

        response = self.client.get(
            self.url,
            {"role": "P", "league": [league1_id, league2_id]},
        )
        assert response.status_code == 200
        assert len(response.data["results"]) == 2

        response = self.client.get(
            self.url,
            {"role": "P", "league": [1111111]},  # fake league_id
        )
        assert response.status_code == 200
        assert len(response.data["results"]) == 0

        count_response = self.client.get(
            self.count_url,
            {"role": "P", "league": [league1_id]},
        )
        assert count_response.status_code == 200
        assert count_response.data["count"] == 1

        count_response = self.client.get(
            self.count_url,
            {"role": "P", "league": [league1_id, league2_id]},
        )
        assert count_response.status_code == 200
        assert count_response.data["count"] == 2

        count_response = self.client.get(
            self.count_url,
            {"role": "P", "league": [1111111]},  # fake league_id
        )
        assert count_response.status_code == 200
        assert count_response.data["count"] == 0

    def test_get_bulk_profiles_filter_localization(self) -> None:
        """test localization filter"""
        start_latitude, start_longitude = 54.25451551801814, 18.315362070454498
        city_a = factories.CityFactory.create(
            name="a", latitude=start_latitude, longitude=start_longitude
        )
        city_b = factories.CityFactory.create(
            name="b", latitude=54.21354701964793, longitude=18.36439364315754
        )
        city_c = factories.CityFactory.create(
            name="c", latitude=54.13695015319587, longitude=18.458313275377453
        )
        factories.PlayerProfileFactory.create(
            user__userpreferences__localization=city_a
        )
        factories.PlayerProfileFactory.create(
            user__userpreferences__localization=city_b
        )
        factories.PlayerProfileFactory.create(
            user__userpreferences__localization=city_c
        )

        response = self.client.get(
            self.url,
            {
                "role": "P",
                "latitude": start_latitude,
                "longitude": start_longitude,
                "radius": 2,
            },
        )
        assert len(response.data["results"]) == 1

        response = self.client.get(
            self.url,
            {
                "role": "P",
                "latitude": start_latitude,
                "longitude": start_longitude,
                "radius": 10,
            },
        )
        assert len(response.data["results"]) == 2

        response = self.client.get(
            self.url,
            {
                "role": "P",
                "latitude": start_latitude,
                "longitude": start_longitude,
                "radius": 20,
            },
        )
        assert len(response.data["results"]) == 3

        count_response = self.client.get(
            self.count_url,
            {
                "role": "P",
                "latitude": start_latitude,
                "longitude": start_longitude,
                "radius": 2,
            },
        )
        assert count_response.data["count"] == 1

        count_response = self.client.get(
            self.count_url,
            {
                "role": "P",
                "latitude": start_latitude,
                "longitude": start_longitude,
                "radius": 10,
            },
        )
        assert count_response.data["count"] == 2

        count_response = self.client.get(
            self.url,
            {
                "role": "P",
                "latitude": start_latitude,
                "longitude": start_longitude,
                "radius": 20,
            },
        )
        assert count_response.data["count"] == 3

    def test_get_bulk_profiles_filter_citizenship(self) -> None:
        """test filter citizenship"""
        factories.PlayerProfileFactory.create(user__userpreferences__citizenship=["PL"])
        factories.PlayerProfileFactory.create(
            user__userpreferences__citizenship=["PL", "UA"]
        )
        factories.PlayerProfileFactory.create(user__userpreferences__citizenship=["DE"])

        response = self.client.get(
            self.url,
            {
                "role": "P",
                "country": ["PL"],
            },
        )
        assert len(response.data["results"]) == 2

        response = self.client.get(
            self.url,
            {
                "role": "P",
                "country": ["UA"],
            },
        )
        assert len(response.data["results"]) == 1

        response = self.client.get(
            self.url,
            {
                "role": "P",
                "country": ["UA", "PL", "DE"],
            },
        )
        assert len(response.data["results"]) == 3

        count_response = self.client.get(
            self.count_url,
            {
                "role": "P",
                "country": ["PL"],
            },
        )
        assert count_response.data["count"] == 2

        count_response = self.client.get(
            self.count_url,
            {
                "role": "P",
                "country": ["UA"],
            },
        )
        assert count_response.data["count"] == 1

        count_response = self.client.get(
            self.count_url,
            {
                "role": "P",
                "country": ["UA", "PL", "DE"],
            },
        )
        assert count_response.data["count"] == 3

    @parameterized.expand([[["Polska"]], [["DE", "Poland"]]])
    def test_get_bulk_profiles_filter_citizenship_invalid_param(
        self, country_codes: list
    ) -> None:
        """test citizenship filter should fail with incorrect param"""
        response = self.client.get(
            self.url,
            {
                "role": "P",
                "country": country_codes,
            },
        )
        assert response.status_code == 400

        count_response = self.client.get(
            self.count_url,
            {
                "role": "P",
                "country": country_codes,
            },
        )
        assert count_response.status_code == 400

    def test_get_bulk_profiles_filter_language(self) -> None:
        """test filter language"""
        factories.PlayerProfileFactory.create_with_language(["pl", "fr"])
        factories.PlayerProfileFactory.create_with_language(["pl", "es"])
        factories.PlayerProfileFactory.create_with_language(["de"])

        response = self.client.get(
            self.url,
            {
                "role": "P",
                "language": ["pl"],
            },
        )
        assert len(response.data["results"]) == 2

        response = self.client.get(
            self.url,
            {
                "role": "P",
                "language": ["de"],
            },
        )
        assert len(response.data["results"]) == 1

        response = self.client.get(
            self.url,
            {
                "role": "P",
                "language": ["fr", "de", "es"],
            },
        )
        assert len(response.data["results"]) == 3

        count_response = self.client.get(
            self.count_url,
            {
                "role": "P",
                "language": ["pl"],
            },
        )
        assert count_response.data["count"] == 2

        count_response = self.client.get(
            self.count_url,
            {
                "role": "P",
                "language": ["de"],
            },
        )
        assert count_response.data["count"] == 1

        count_response = self.client.get(
            self.count_url,
            {
                "role": "P",
                "language": ["fr", "de", "es"],
            },
        )
        assert count_response.data["count"] == 3

    @parameterized.expand([[["polski"]], [["DE", "Polish"]]])
    def test_get_bulk_profiles_filter_language_invalid_param(
        self, country_codes: list
    ) -> None:
        """test language filter should fail with incorrect param"""
        response = self.client.get(
            self.url,
            {
                "role": "P",
                "country": country_codes,
            },
        )
        assert response.status_code == 400

        count_response = self.client.get(
            self.count_url,
            {
                "role": "P",
                "country": country_codes,
            },
        )
        assert count_response.status_code == 400

    def test_get_bulk_profiles_filter_licence(self) -> None:
        """test filter licence"""
        player_profile = factories.PlayerProfileFactory.create()
        licence_type = LicenceType.objects.get(name="UEFA PRO")
        licence = factories.CoachLicenceFactory(
            owner=player_profile.user, licence=licence_type
        )

        response = self.client.get(
            self.url,
            {
                "role": "P",
                "licence": [licence.licence.name],
            },
        )
        assert len(response.data["results"]) == 1

        count_response = self.client.get(
            self.count_url,
            {
                "role": "P",
                "licence": [licence.licence.name],
            },
        )
        assert count_response.data["count"] == 1

    def test_get_bulk_profiles_filter_licence_invalid(self) -> None:
        """
        Test the filter licence functionality with an invalid licence name to
         ensure that the validation logic works correctly and the API
         responds appropriately.
        """
        factories.PlayerProfileFactory.create()
        invalid_licence_name = "INVALID_LICENCE"
        response = self.client.get(
            self.url,
            {
                "role": "P",
                "licence": [invalid_licence_name],
            },
        )

        assert response.status_code == 400
        expected_error_msg = (
            "Invalid value for field: licence in model: "
            "LicenceType. Field must be one of:"
        )
        assert expected_error_msg in response.data["detail"]

        count_response = self.client.get(
            self.count_url,
            {
                "role": "P",
                "licence": [invalid_licence_name],
            },
        )

        assert count_response.status_code == 400
        expected_error_msg = (
            "Invalid value for field: licence in model: "
            "LicenceType. Field must be one of:"
        )
        assert expected_error_msg in count_response.data["detail"]

    def test_get_bulk_profiles_filter_by_labels(self) -> None:
        """Test profile filtering by labels"""
        # Create label definitions and labels
        label_def1 = LabelDefinitionFactory(label_name="Label1")
        label_def2 = LabelDefinitionFactory(label_name="Label2")

        # Create profiles with labels
        profile_with_label1 = factories.PlayerProfileFactory()
        LabelFactory(label_definition=label_def1, content_object=profile_with_label1)

        profile_with_label2 = factories.PlayerProfileFactory()
        LabelFactory(label_definition=label_def2, content_object=profile_with_label2)

        # Test filtering by Label1
        response = self.client.get(
            self.url, {"role": "P", "labels": "Label1"}, **self.headers
        )
        assert response.status_code == 200
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["uuid"] == str(profile_with_label1.uuid)

        # Test filtering by Label2
        response = self.client.get(
            self.url, {"role": "P", "labels": "Label2"}, **self.headers
        )
        assert response.status_code == 200
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["uuid"] == str(profile_with_label2.uuid)

        # Test filtering with a label that no profile has
        response = self.client.get(
            self.url, {"role": "P", "labels": "Label3"}, **self.headers
        )
        assert response.status_code == 200
        assert len(response.data["results"]) == 0

        count_response = self.client.get(
            self.count_url, {"role": "P", "labels": "Label1"}, **self.headers
        )
        assert count_response.status_code == 200
        assert count_response.data["count"] == 1

        count_response = self.client.get(
            self.count_url, {"role": "P", "labels": "Label2"}, **self.headers
        )
        assert count_response.status_code == 200
        assert count_response.data["count"] == 1

        count_response = self.client.get(
            self.count_url, {"role": "P", "labels": "Label3"}, **self.headers
        )
        assert count_response.status_code == 200
        assert response.data["count"] == 0

    def test_get_bulk_profiles_with_transfer_status(self) -> None:
        """
        Test the ability to filter player profiles based on transfer status.

        This test verifies the functionality of the transfer status filter by
        creating player profiles with different transfer statuses and then making API
        requests to filter these profiles based on their transfer status. The test cases
        cover filtering by a single status, multiple statuses, and the special case of
        status "5" which represents profiles without an associated transfer
        status object.
        """
        # Create profiles with various transfer statuses
        player_with_status_1 = PlayerProfileFactory.create()
        TransferStatusFactory.create(profile=player_with_status_1, status="1")

        player_with_status_2 = PlayerProfileFactory.create()
        TransferStatusFactory.create(profile=player_with_status_2, status="2")

        PlayerProfileFactory.create()

        # Test filtering for status "1"
        response = self.client.get(
            self.url, {"role": "P", "transfer_status": "1"}, **self.headers
        )
        assert response.status_code == 200
        assert (
            len(response.data["results"]) == 1
        )  # Only player_with_status_1 should be returned

        # Test filtering for status "2"
        response = self.client.get(
            self.url, {"role": "P", "transfer_status": "2"}, **self.headers
        )
        assert response.status_code == 200
        assert (
            len(response.data["results"]) == 1
        )  # Only player_with_status_2 should be returned

        # Test filtering for status "5" (no transfer status)
        response = self.client.get(
            self.url, {"role": "P", "transfer_status": "5"}, **self.headers
        )
        assert response.status_code == 200
        assert (
            len(response.data["results"]) == 1
        )  # Only player_without_transfer_status should be returned

        # Test filtering for status "1" and "2"
        response = self.client.get(
            self.url, {"role": "P", "transfer_status": ["1", "2"]}, **self.headers
        )
        assert response.status_code == 200
        assert (
            len(response.data["results"]) == 2
        )  # player_with_status_1 and player_with_status2 should be returned

        # Test filtering for status "1" and "5"
        response = self.client.get(
            self.url, {"role": "P", "transfer_status": ["1", "5"]}, **self.headers
        )
        assert response.status_code == 200
        assert (
            len(response.data["results"]) == 2
        )  # player_with_status_1 and player_without_transfer_status should be returned

    def test_filter_profiles_by_transfer_status_league(self) -> None:
        """
        Test the ability to filter player profiles based on their associated leagues.

        This test verifies that profiles can be correctly filtered by the league associated
        with their transfer status. It creates two profiles each linked to a different league,
        then performs an API request to filter by one of the leagues and checks if the response
        contains only the profile associated with that league.
        """
        # Create leagues
        league1 = LeagueFactory.create()
        league2 = LeagueFactory.create()

        # Create profiles with transfer statuses linked to different leagues
        player_in_league1 = PlayerProfileFactory.create()
        TransferStatusFactory.create(
            profile=player_in_league1, leagues=[league1]
        )  # Pass league instance

        player_in_league2 = PlayerProfileFactory.create()
        TransferStatusFactory.create(
            profile=player_in_league2, leagues=[league2]
        )  # Pass league instance

        # Perform API request to filter by league1
        response = self.client.get(
            self.url, {"role": "P", "transfer_status_league": league1.id}, **self.headers
        )
        assert response.status_code == 200
        assert len(response.data["results"]) == 1

    def test_filter_profiles_by_additional_info(self) -> None:
        """
        Test the ability to filter player profiles based on additional information in their transfer status.

        This test checks if profiles can be filtered based on specific additional information
        identifiers associated with their transfer status. It ensures that the API correctly
        returns profiles matching the requested additional information.
        """
        player_with_additional_info = PlayerProfileFactory.create()
        TransferStatusFactory.create(
            profile=player_with_additional_info, additional_info=["1", "2"]
        )

        player_without_additional_info = PlayerProfileFactory.create()
        TransferStatusFactory.create(
            profile=player_without_additional_info, additional_info=[]
        )

        # Filter for profiles with specific additional info
        response = self.client.get(
            self.url, {"role": "P", "additional_info": "1"}, **self.headers
        )
        assert response.status_code == 200
        assert len(response.data["results"]) == 1

    def test_filter_profiles_by_number_of_trainings(self) -> None:
        """
        Test the ability to filter player profiles based on the number of trainings per week specified in their transfer status.

        This test creates profiles with specified training frequencies in their transfer status
        and checks if the API can filter these profiles based on the given number of trainings.
        """
        player_with_trainings = PlayerProfileFactory.create()
        TransferStatusFactory.create(
            profile=player_with_trainings, number_of_trainings="1"
        )

        # Filter for profiles with specific number of trainings
        response = self.client.get(
            self.url, {"role": "P", "number_of_trainings": "1"}, **self.headers
        )
        assert response.status_code == 200
        assert len(response.data["results"]) == 1

    def test_filter_profiles_by_benefits(self) -> None:
        """
        Test the ability to filter player profiles based on the benefits mentioned in their transfer status.

        This test verifies the functionality of filtering profiles by specific benefits.
        It creates profiles with varying benefits in their transfer status and checks if
        the API accurately filters profiles based on these benefits.
        """
        player_with_benefits = PlayerProfileFactory.create()
        TransferStatusFactory.create(profile=player_with_benefits, benefits=["1", "2"])

        # Filter for profiles with specific benefits
        response = self.client.get(
            self.url, {"role": "P", "benefits": "1"}, **self.headers
        )
        assert response.status_code == 200
        assert len(response.data["results"]) == 1

    def test_filter_profiles_by_salary(self) -> None:
        """
        Test the ability to filter player profiles based on the salary range specified in their transfer status.

        This test checks if the API can accurately filter profiles based on the salary range
        defined in their transfer status, ensuring that only profiles matching the specified
        salary criteria are returned in the response.
        """
        player_with_salary = PlayerProfileFactory.create()
        TransferStatusFactory.create(profile=player_with_salary, salary="1")

        # Filter for profiles with specific salary
        response = self.client.get(
            self.url, {"role": "P", "salary": "1"}, **self.headers
        )
        assert response.status_code == 200
        assert len(response.data["results"]) == 1


@override_settings(SUSPEND_SIGNALS=True)
class TestPlayerProfileListByGenderAPI(APITestCase):
    """Test profile/ url with gender parameters."""

    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.url = reverse(url)
        self.count_url = reverse(count_url)

    @parameterized.expand(
        [
            [{"role": "P", "gender": "K"}],
            [{"role": "P", "gender": "M"}],
            [{"role": "P", "gender": "Male"}],
        ]
    )
    def test_get_bulk_profiles_by_gender(self, param) -> None:
        """get profiles by gender"""
        PlayerProfileFactory.create_batch(10)

        response: Response = self.client.get(self.url, param)
        expected_count: int = PlayerProfile.objects.filter(
            user__userpreferences__gender=param["gender"]
        ).count()

        assert len(response.data["results"]) == expected_count
        assert response.status_code == 200

        count_response: Response = self.client.get(self.count_url, param)

        assert count_response.data["count"] == expected_count
        assert count_response.status_code == 200

    @parameterized.expand(
        [[{"role": "P", "gender": "K"}], [{"role": "P", "gender": "M"}]]
    )
    def test_get_bulk_profiles_by_gender_res_0(self, param) -> None:
        """get profiles by gender. Result should be 0"""
        PlayerProfileFactory.create_batch(10, user__userpreferences__gender=None)
        response = self.client.get(self.url, param)

        assert len(response.data["results"]) == 0
        assert response.status_code == 200

        count_response = self.client.get(self.count_url, param)

        assert count_response.data["count"] == 0
        assert count_response.status_code == 200


@pytest.mark.django_db
@mock.patch.object(
    ProfileManager,
    "get_data_score",
    side_effect=lambda obj: random.randint(1, 3),
)
def test_if_response_is_ordered_by_data_score(
    data_fulfill_score: MagicMock,  # noqa # pylint: disable=unused-argument
    api_client: APIClient,
) -> None:
    """
    Test if response is ordered by data_fulfill_score.
    We are mocking here data_fulfill_score method.
    Endpoint returns 10 results, so we can guess how response will look like
    """
    profiles: List[PlayerProfile] = PlayerProfileFactory.create_batch(5)

    expected_response = [
        obj.data_fulfill_status
        for obj in sorted(profiles, key=lambda x: x.data_fulfill_status)
    ]

    response: Response = api_client.get(reverse(url) + "?role=P")
    user_ids_response = [obj["user"]["id"] for obj in response.data["results"]]

    profiles_scoring = [
        var["data_fulfill_status"]
        for var in list(
            PlayerProfile.objects.filter(user__in=user_ids_response).values(
                "data_fulfill_status"
            )
        )
    ]
    assert expected_response == sorted(map(int, profiles_scoring))


@factory.django.mute_signals(signals.pre_save, signals.post_save)
@pytest.mark.django_db
@mock.patch.object(
    ProfileManager,
    "get_data_score",
    side_effect=lambda obj: random.randint(1, 3),
)
def test_if_response_is_ordered_by_data_score_with_many_profiles(
    data_fulfill_score: MagicMock,  # noqa # pylint: disable=unused-argument
    api_client: APIClient,
) -> None:
    """
    Test if response is ordered by data_fulfill_score.
    We are mocking here data_fulfill_score method.
    Endpoint returns 10 items, and we are creating 50 profiles.
    We can't guess how response would look like.
    """
    PlayerProfileFactory.create_batch(20)
    response: Response = api_client.get(reverse(url) + "?role=P")
    user_ids_response = [obj["user"]["id"] for obj in response.data["results"]]

    # Get profiles data_fulfill_status level
    profiles_scoring = []
    for element in user_ids_response:
        profiles_scoring.append(
            PlayerProfile.objects.get(pk=element).data_fulfill_status
        )

    expected_response = sorted(profiles_scoring)

    # We have to check if sorted list is equal as the response one
    assert expected_response == profiles_scoring


@pytest.mark.django_db
def test_profile_listing_not_me_parameter(api_client: APIClient) -> None:
    """Test if user profile is not returned when not_me parameter is set to true"""
    user = UserFactory.create(password="test1234")
    PlayerProfileFactory.create(user=user)

    user_manager = UserManager(api_client)
    headers = user_manager.custom_user_headers(email=user.email, password="test1234")
    url_to_hit: str = reverse(url)
    response_without_my_profile = api_client.get(
        url_to_hit + "?role=P&not_me=true", **headers
    )
    response_with_profile = api_client.get(url_to_hit + "?role=P", **headers)

    assert len(response_without_my_profile.data["results"]) == 0
    assert len(response_with_profile.data["results"]) == 1


@pytest.mark.django_db
def test_profile_listing_not_me_wrong_parameter(api_client: APIClient) -> None:
    """Test if user profile is not returned when not_me parameter is set to true"""
    user = UserFactory.create(password="test1234")
    PlayerProfileFactory.create(user=user)

    user_manager = UserManager(api_client)
    headers = user_manager.custom_user_headers(email=user.email, password="test1234")
    url_to_hit: str = reverse(url)
    response_wit_not_me_param = api_client.get(
        url_to_hit + "?role=P&not_me=false", **headers
    )
    response_with_profile = api_client.get(url_to_hit + "?role=P", **headers)

    assert len(response_wit_not_me_param.data["results"]) == 1
    assert len(response_with_profile.data["results"]) == 1
