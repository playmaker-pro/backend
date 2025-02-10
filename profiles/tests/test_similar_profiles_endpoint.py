from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from utils import factories
from utils.factories import CityFactory

url = "api:profiles:get_suggested_profiles"
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
    user = factories.UserFactory.create()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def coach(city_wwa):
    return factories.CoachProfileFactory.create(
        user__userpreferences__gender="M",
        coach_role="IC",
        user__userpreferences__localization=city_wwa,
    )


@pytest.fixture
def player(city_wwa):
    p = factories.PlayerProfileFactory.create(
        user__userpreferences__gender="M",
        user__userpreferences__localization=city_wwa,
    )

    factories.PlayerProfilePositionFactory.create(
        player_profile=p,
        player_position=factories.PlayerPositionFactory.create(name="CAM"),
        is_main=True,
    )
    return p


class TestSimilarProfilesAPI:
    def test_get_suggested_profiles_for_player(
        self, player, api_client, city_wwa
    ) -> None:
        """
        Test retrieving similar profiles for a player profile with the same position.
        """

        clubs = [
            factories.ClubProfileFactory.create(
                user__last_activity=time_now,
                user__userpreferences__localization=city_wwa,
            )
            for _ in range(5)
        ]
        coaches = [
            factories.CoachProfileFactory.create(
                user__last_activity=time_now,
                user__userpreferences__localization=city_wwa,
            )
            for _ in range(5)
        ]

        similar_profile_url = reverse(
            url,
            kwargs={"profile_uuid": player.uuid},
        )
        response = api_client.get(similar_profile_url)
        slugs = [dict(item)["slug"] for item in response.data]

        assert response.status_code == 200
        assert len(response.data) == 10

        for coach in coaches:
            assert coach.slug in slugs

        for club in clubs:
            assert club.slug in slugs

    def test_get_suggested_profiles_for_others(
        self, coach, api_client, city_wwa
    ) -> None:
        """
        Test retrieving similar profiles for a coach profile with the same coach role.
        """
        players = [
            factories.PlayerProfileFactory.create(
                user__last_activity=time_now,
                user__userpreferences__localization=city_wwa,
            )
            for _ in range(10)
        ]

        # Test API endpoint
        similar_profile_url = reverse(
            url,
            kwargs={"profile_uuid": coach.uuid},
        )
        response = api_client.get(similar_profile_url)
        slugs = [dict(item)["slug"] for item in response.data]

        assert response.status_code == 200
        assert len(response.data) == 10

        for player in players:
            assert player.slug in slugs

    def test_suggested_profiles_for_player_choice(
        self, city_wwa, city_prsk, api_client, player
    ):
        """
        Test retrieving similar profiles for a player profile with no main position.
        """

        some_player = factories.PlayerProfileFactory.create(
            user__userpreferences__localization=city_wwa
        )
        some_coach = factories.CoachProfileFactory.create(
            user__userpreferences__localization=city_wwa,
            user__last_activity=time_now,
        )
        some_club = factories.ClubProfileFactory.create(
            user__userpreferences__localization=city_prsk,
            user__last_activity=time_now,
        )
        similar_profile_url = reverse(
            url,
            kwargs={"profile_uuid": player.uuid},
        )
        response = api_client.get(similar_profile_url)

        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]["slug"] == some_coach.slug
        assert response.data[1]["slug"] == some_club.slug

    def test_suggested_profiles_for_player_choice2(
        self, city_wwa, city_prsk, city_rdm, api_client, player
    ):
        """
        Test retrieving similar profiles for a player profile with no main position.
        """

        some_player = factories.PlayerProfileFactory.create(
            user__userpreferences__localization=city_wwa
        )
        some_coach = factories.CoachProfileFactory.create(
            user__userpreferences__localization=city_rdm,
            user__last_activity=time_now,
        )
        some_club = factories.ClubProfileFactory.create(
            user__userpreferences__localization=city_prsk,
            user__last_activity=time_now,
        )
        similar_profile_url = reverse(
            url,
            kwargs={"profile_uuid": player.uuid},
        )
        response = api_client.get(similar_profile_url)

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["slug"] == some_club.slug

    def test_suggested_profiles_for_player_choice3(
        self, city_wwa, city_prsk, api_client, player
    ):
        """
        Test retrieving similar profiles for a player profile with no main position.
        """

        some_player = factories.PlayerProfileFactory.create(
            user__userpreferences__localization=city_wwa
        )
        some_coach = factories.CoachProfileFactory.create(
            user__userpreferences__localization=city_wwa,
            user__last_activity=time_now - timedelta(days=11),
        )
        some_club = factories.ClubProfileFactory.create(
            user__userpreferences__localization=city_prsk,
            user__last_activity=time_now,
        )

        similar_profile_url = reverse(
            url,
            kwargs={"profile_uuid": str(player.uuid)},
        )
        response = api_client.get(similar_profile_url)

        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]["slug"] == some_coach.slug
        assert response.data[1]["slug"] == some_club.slug

    def test_suggested_profiles_for_others_choice(
        self, city_wwa, city_prsk, api_client, coach
    ):
        """
        Test retrieving similar profiles for a player profile with no main position.
        """
        some_player = factories.PlayerProfileFactory.create(
            user__userpreferences__localization=city_wwa,
            user__last_activity=time_now - timedelta(days=28),
        )
        some_player2 = factories.PlayerProfileFactory.create(
            user__userpreferences__localization=city_prsk,
            user__last_activity=time_now,
        )
        some_player3 = factories.PlayerProfileFactory.create(
            user__userpreferences__localization=city_wwa,
            user__last_activity=time_now,
        )
        some_player4 = factories.PlayerProfileFactory.create(
            user__userpreferences__localization=city_prsk,
            user__last_activity=time_now - timedelta(days=1),
        )
        some_coach = factories.CoachProfileFactory.create(
            user__userpreferences__localization=city_wwa,
            user__last_activity=time_now,
        )

        similar_profile_url = reverse(
            url,
            kwargs={"profile_uuid": coach.uuid},
        )
        response = api_client.get(similar_profile_url)

        assert response.status_code == 200
        assert len(response.data) == 4
        assert response.data[0]["slug"] == some_player3.slug
        assert response.data[1]["slug"] == some_player.slug
        assert response.data[2]["slug"] == some_player2.slug
        assert response.data[3]["slug"] == some_player4.slug

    def test_suggested_profiles_for_others_choice2(self, city_wwa, api_client, coach):
        """
        Test retrieving similar profiles for a player profile with no main position.
        """

        some_player = factories.PlayerProfileFactory.create(
            user__userpreferences__localization=city_wwa,
            user__last_activity=time_now - timedelta(days=11),
        )
        some_player2 = factories.PlayerProfileFactory.create(
            user__userpreferences__localization=city_wwa,
            user__last_activity=time_now - timedelta(days=1),
        )

        similar_profile_url = reverse(
            url,
            kwargs={"profile_uuid": coach.uuid},
        )
        response = api_client.get(similar_profile_url)

        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]["slug"] == some_player2.slug
        assert response.data[1]["slug"] == some_player.slug

    def test_suggested_profiles_for_others_choice3(self, city_wwa, coach, api_client):
        """
        Test retrieving similar profiles for a player profile with no main position.
        """
        some_player = factories.PlayerProfileFactory.create(
            user__userpreferences__localization=city_wwa
        )
        some_player2 = factories.PlayerProfileFactory.create(
            user__userpreferences__localization=city_wwa,
            user__last_activity=time_now - timedelta(days=11),
        )

        similar_profile_url = reverse(
            url,
            kwargs={"profile_uuid": coach.uuid},
        )
        response = api_client.get(similar_profile_url)

        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]["slug"] == some_player.slug
        assert response.data[1]["slug"] == some_player2.slug
