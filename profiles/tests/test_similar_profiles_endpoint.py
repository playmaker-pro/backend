from datetime import timedelta
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from profiles.models import CoachProfile
from utils import factories
from utils.factories import CityFactory

url_suggested_profiles = "api:profiles:get_suggested_profiles"
url_profiles_near_me = "api:profiles:get_profiles_near_me"
time_now = timezone.now()
pytestmark = pytest.mark.django_db


@pytest.fixture()
def city_wwa():
    return CityFactory.create_with_coordinates(
        name="Warsaw",
        coordinates=(21.0122, 52.2297),
    )


@pytest.fixture
def city_prsk():
    return CityFactory.create_with_coordinates(
        name="Pruszków",
        coordinates=(20.8072, 52.1684),
    )


@pytest.fixture
def city_rdm():
    return CityFactory.create_with_coordinates(
        name="Radom", coordinates=(21.1572, 51.4025)
    )


@pytest.fixture
def api_client():
    client: APIClient = APIClient()
    return client


class TestSimilarProfilesAPI:
    def test_get_suggested_profiles_for_player(self, api_client, city_wwa) -> None:
        """
        Test retrieving similar profiles for a player profile with the same position.
        """
        user = factories.PlayerProfileFactory(
            user__userpreferences__localization=city_wwa
        ).user
        api_client.force_authenticate(user)
        params = {
            "user__last_activity": timezone.now(),
            "user__userpreferences__localization": city_wwa,
        }
        choices = [
            factories.ClubProfileFactory.create(**params),
            factories.CoachProfileFactory.create(**params),
            factories.ScoutProfileFactory.create(**params),
        ]
        uuid_choices = [str(choice.uuid) for choice in choices]
        similar_profile_url = reverse(
            url_suggested_profiles,
        )
        response = api_client.get(similar_profile_url)

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.json()[0]["uuid"] in uuid_choices

    def test_get_suggested_profiles_for_others(self, api_client, city_wwa) -> None:
        """
        Test retrieving similar profiles for a coach profile with the same coach role.
        """

        user = factories.CoachProfileFactory(
            user__userpreferences__localization=city_wwa
        ).user
        api_client.force_authenticate(user)
        players = [
            factories.PlayerProfileFactory.create(
                user__last_activity=timezone.now(),
                user__userpreferences__localization=city_wwa,
            )
            for _ in range(2)
        ]
        _ = [
            factories.PlayerProfileFactory.create() for _ in range(2)
        ]  # no loc players
        uuids = [str(player.uuid) for player in players]
        similar_profile_url = reverse(
            url_suggested_profiles,
        )
        response = api_client.get(similar_profile_url)

        assert response.status_code == 200
        assert len(response.data) == 2

        for uuid in [profile["uuid"] for profile in response.data]:
            assert uuid in uuids

    def test_get_suggested_profiles_for_player2(
        self,
        city_wwa,
        city_prsk,
        city_rdm,
        api_client,
    ):
        user = factories.PlayerProfileFactory(
            user__userpreferences__localization=city_wwa
        ).user
        api_client.force_authenticate(user)

        choices = [
            factories.CoachProfileFactory.create(
                user__last_activity=timezone.now(),
                user__userpreferences__localization=city_wwa,
            ),
            factories.CoachProfileFactory.create(
                user__last_activity=timezone.now(),
                user__userpreferences__localization=city_prsk,
            ),
            factories.CoachProfileFactory.create(
                user__last_activity=timezone.now(),
                user__userpreferences__localization=city_rdm,
            ),
            factories.CoachProfileFactory.create(
                user__last_activity=timezone.now() - timedelta(days=1),
                user__userpreferences__localization=city_wwa,
            ),
            factories.CoachProfileFactory.create(
                user__last_activity=timezone.now() - timedelta(days=1),
                user__userpreferences__localization=city_prsk,
            ),
            factories.CoachProfileFactory.create(
                user__last_activity=timezone.now() - timedelta(days=1),
                user__userpreferences__localization=city_rdm,
            ),
            factories.CoachProfileFactory.create(
                user__last_activity=timezone.now() - timedelta(days=40),
                user__userpreferences__localization=city_wwa,
            ),
            factories.CoachProfileFactory.create(
                user__last_activity=timezone.now() - timedelta(days=40),
                user__userpreferences__localization=city_prsk,
            ),
            factories.CoachProfileFactory.create(
                user__last_activity=timezone.now() - timedelta(days=40),
                user__userpreferences__localization=city_rdm,
            ),
        ]
        uuids = [str(choice.uuid) for choice in choices[:6]]

        similar_profile_url = reverse(
            url_suggested_profiles,
        )
        with patch("random.choice", return_value=CoachProfile):
            response = api_client.get(similar_profile_url)
            data = response.data

            assert response.status_code == 200
            assert len(response.data) == 4
            assert data[0]["uuid"] == uuids[0]
            assert data[1]["uuid"] == uuids[3]
            assert data[2]["uuid"] == uuids[1]
            assert data[3]["uuid"] == uuids[4]

    def test_get_suggested_profiles_for_other2(
        self, city_wwa, city_prsk, city_rdm, api_client
    ):
        user = factories.CoachProfileFactory(
            user__userpreferences__localization=city_wwa
        ).user
        api_client.force_authenticate(user)

        choices = [
            factories.PlayerProfileFactory.create(
                user__last_activity=timezone.now(),
                user__userpreferences__localization=city_wwa,
            ),
            factories.PlayerProfileFactory.create(
                user__last_activity=timezone.now(),
                user__userpreferences__localization=city_prsk,
            ),
            factories.PlayerProfileFactory.create(  # NOPE
                user__last_activity=timezone.now(),
                user__userpreferences__localization=city_rdm,
            ),
            factories.PlayerProfileFactory.create(
                user__last_activity=timezone.now() - timedelta(days=1),
                user__userpreferences__localization=city_wwa,
            ),
            factories.PlayerProfileFactory.create(
                user__last_activity=timezone.now() - timedelta(days=1),
                user__userpreferences__localization=city_prsk,
            ),
            factories.PlayerProfileFactory.create(  # NOPE
                user__last_activity=timezone.now() - timedelta(days=1),
                user__userpreferences__localization=city_rdm,
            ),
            factories.PlayerProfileFactory.create(  # NOPE
                user__last_activity=timezone.now() - timedelta(days=40),
                user__userpreferences__localization=city_wwa,
            ),
            factories.PlayerProfileFactory.create(  # NOPE
                user__last_activity=timezone.now() - timedelta(days=40),
                user__userpreferences__localization=city_prsk,
            ),
            factories.PlayerProfileFactory.create(  # NOPE
                user__last_activity=timezone.now() - timedelta(days=40),
                user__userpreferences__localization=city_rdm,
            ),
        ]
        uuids = [str(choice.uuid) for choice in choices[:6]]

        similar_profile_url = reverse(
            url_suggested_profiles,
        )
        response = api_client.get(similar_profile_url)
        data = response.data
        assert response.status_code == 200
        assert len(response.data) == 4

    def test_get_profiles_nearby(
        self,
        city_wwa,
        city_prsk,
        city_rdm,
        api_client,
    ):
        user = factories.PlayerProfileFactory(
            user__userpreferences__localization=city_wwa
        ).user
        api_client.force_authenticate(user)

        choices = [
            factories.PlayerProfileFactory.create(
                user__last_activity=timezone.now(),
                user__userpreferences__localization=city_wwa,
            ),
            factories.CoachProfileFactory.create(
                user__last_activity=timezone.now(),
                user__userpreferences__localization=city_prsk,
            ),
            factories.CoachProfileFactory.create(
                user__last_activity=timezone.now(),
                user__userpreferences__localization=city_rdm,
            ),
        ]

        url = reverse(
            url_profiles_near_me,
        )
        response = api_client.get(url)
        data = response.data
        assert response.status_code == 200
        assert len(data) == 2
        assert data[0]["uuid"] == str(choices[0].uuid)
        assert data[1]["uuid"] == str(choices[1].uuid)
