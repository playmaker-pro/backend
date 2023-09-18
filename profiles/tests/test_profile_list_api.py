from typing import List

import factory
from django.urls import reverse
from parameterized import parameterized
from rest_framework.response import Response
from rest_framework.test import APIClient, APITestCase

from profiles.models import PlayerProfile
from profiles.services import ProfileService
from profiles.utils import get_past_date
from users.models import UserPreferences
from utils import factories, get_current_season
from utils.factories import PlayerProfileFactory, UserPreferencesFactory
from utils.test.test_utils import UserManager

profile_service = ProfileService()
url_get_create_or_update: str = "api:profiles:get_create_or_update_profile"


class TestProfileListAPI(APITestCase):
    def setUp(self) -> None:
        """set up object factories"""
        self.client: APIClient = APIClient()
        self.user = UserManager(self.client)
        self.user_obj = self.user.create_superuser()
        self.headers = self.user.get_headers()
        self.url = reverse(url_get_create_or_update)

    def test_shuffle_list(self) -> None:
        """Test if results are correctly shuffled"""
        factories.PlayerProfileFactory.create_batch(10)
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

    @parameterized.expand([[{}], [{"role": "Piłkarz"}], [{"role": "p"}]])
    def test_get_bulk_profiles_invalid_param(self, param) -> None:
        """get profiles by invalid role param"""
        response = self.client.get(self.url, param, **self.headers)

        assert response.status_code == 400

    def test_get_bulk_profiles_youth_only(self) -> None:
        """get only youth player profiles"""
        youth_birth_date = get_past_date(years=20)
        factories.PlayerProfileFactory.create_with_birth_date(youth_birth_date)  # youth
        factories.PlayerProfileFactory.create_with_birth_date("1995-04-21")  # not youth

        response = self.client.get(
            self.url, {"role": "P", "youth": "true"}, **self.headers
        )

        assert response.status_code == 200
        assert len(response.data["results"]) == 1

    def test_get_bulk_profiles_filter_age(self) -> None:
        """get player profiles with age between"""
        too_young_birth_year = get_past_date(years=20)
        exact_birth_year = get_past_date(years=25)
        too_old_birth_year = get_past_date(years=30)
        factories.PlayerProfileFactory.create_with_birth_date(too_young_birth_year)
        factories.PlayerProfileFactory.create_with_birth_date(exact_birth_year)
        factories.PlayerProfileFactory.create_with_birth_date(too_old_birth_year)

        response = self.client.get(
            self.url, {"role": "P", "min_age": "22", "max_age": "27"}, **self.headers
        )

        assert response.status_code == 200
        assert len(response.data["results"]) == 1

    def test_get_bulk_profiles_filter_position(self) -> None:
        """get player profiles filter by position"""
        factories.PlayerProfileFactory.create_with_position("CAM")
        factories.PlayerProfileFactory.create_with_position("GK")

        response = self.client.get(
            self.url,
            {"role": "P", "position": "CAM"},
        )
        assert response.status_code == 200
        assert len(response.data["results"]) == 1

        response = self.client.get(
            self.url,
            {"role": "P", "position": ["CAM", "GK"]},
        )
        assert response.status_code == 200
        assert len(response.data["results"]) == 2

    def test_get_bulk_profiles_filter_league(self) -> None:
        """get player profiles filter by league"""
        current_season = get_current_season()
        th1, th2 = factories.TeamHistoryFactory.create_batch(
            2, league_history__season__name=current_season
        )

        profile1 = factories.PlayerProfileFactory.create(team_object=th1.team)
        profile2 = factories.PlayerProfileFactory.create(team_object=th2.team)
        league1_id = profile1.team_object.latest_league_from_lh.highest_parent.id
        league2_id = profile2.team_object.latest_league_from_lh.highest_parent.id

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
        factories.PlayerProfileFactory.create_with_localization(city_a)
        factories.PlayerProfileFactory.create_with_localization(city_b)
        factories.PlayerProfileFactory.create_with_localization(city_c)

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

    def test_get_bulk_profiles_filter_citizenship(self) -> None:
        """test filter citizenship"""
        factories.PlayerProfileFactory.create_with_citizenship(["PL"])
        factories.PlayerProfileFactory.create_with_citizenship(["PL", "UA"])
        factories.PlayerProfileFactory.create_with_citizenship(["DE"])

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


class TestPlayerProfileListByGenderAPI(APITestCase):
    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.url = reverse(url_get_create_or_update)

    @parameterized.expand(
        [
            [{"role": "P", "gender": "K"}],
            [{"role": "P", "gender": "M"}],
            [{"role": "P", "gender": "Male"}],
        ]
    )
    def test_get_bulk_profiles_by_gender(self, param) -> None:
        """get profiles by gender"""
        profiles: List[PlayerProfile] = PlayerProfileFactory.create_batch(10)
        UserPreferencesFactory.create_batch(
            10, user=factory.Sequence(lambda n: profiles[n % 10].user)
        )

        response: Response = self.client.get(self.url, param)
        expected_count: int = UserPreferences.objects.filter(
            gender=param["gender"]
        ).count()

        assert len(response.data["results"]) == expected_count
        assert response.status_code == 200

    @parameterized.expand(
        [[{"role": "P", "gender": "K"}], [{"role": "P", "gender": "M"}]]
    )
    def test_get_bulk_profiles_by_gender_res_0(self, param) -> None:
        """get profiles by gender. Result should be 0"""
        profiles: List[PlayerProfile] = PlayerProfileFactory.create_batch(10)
        UserPreferencesFactory.create_batch(
            10, user=factory.Sequence(lambda n: profiles[n % 10].user), gender=None
        )

        response = self.client.get(self.url, param)

        assert len(response.data["results"]) == 0
        assert response.status_code == 200
