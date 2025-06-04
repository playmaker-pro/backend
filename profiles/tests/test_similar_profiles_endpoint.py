from datetime import timedelta
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone

from profiles.models import CoachProfile
from utils import factories
from utils.factories.profiles_factories import GuestProfileFactory, PlayerProfileFactory

url_suggested_profiles = "api:profiles:get_suggested_profiles"
url_profiles_near_me = "api:profiles:get_profiles_near_me"
time_now = timezone.now()
pytestmark = pytest.mark.django_db


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
        data = response.data["results"]
        assert response.status_code == 200
        assert response.data["count"] == 2
        assert data[0]["uuid"] == str(choices[0].uuid)
        assert data[1]["uuid"] == str(choices[1].uuid)

    @pytest.mark.parametrize("roles", (["T", "S"], ["P"], ["P", "T", "S"]))
    def test_get_profiles_nearby_filter_role(
        self, player_profile, coach_profile, scout_profile, api_client, roles, city_wwa
    ):
        for profile in [player_profile, coach_profile, scout_profile]:
            profile.user.userpreferences.localization = city_wwa
            profile.user.userpreferences.save()
        user = factories.PlayerProfileFactory(
            user__userpreferences__localization=city_wwa
        ).user
        api_client.force_authenticate(user)
        url = reverse(
            url_profiles_near_me,
        )
        response = api_client.get(url, {"role": roles})

        assert response.status_code == 200
        assert response.data["count"] == len(roles)

    @pytest.mark.parametrize("gender", (["M"], ["K"], ["M", "K"]))
    def test_get_profiles_nearby_filter_gender(self, api_client, gender, city_wwa):
        profile = PlayerProfileFactory.create(
            user__userpreferences__localization=city_wwa,
        )
        GuestProfileFactory.create(
            user__userpreferences__localization=city_wwa,
            user__userpreferences__gender="M",
        )
        GuestProfileFactory.create(
            user__userpreferences__localization=city_wwa,
            user__userpreferences__gender="K",
        )
        api_client.force_authenticate(profile.user)
        url = reverse(
            url_profiles_near_me,
        )
        response = api_client.get(url, {"gender": gender, "role": "G"})

        assert response.status_code == 200
        assert response.data["count"] == len(gender)

    def test_get_profiles_nearby_filter_age(self, api_client, city_wwa):
        g1 = GuestProfileFactory.create(
            user__userpreferences__localization=city_wwa,
            user__userpreferences__birth_date=timezone.now()
            - timedelta(days=365 * 20),  # 20 years old
        )
        g2 = GuestProfileFactory.create(
            user__userpreferences__localization=city_wwa,
            user__userpreferences__birth_date=timezone.now()
            - timedelta(days=365 * 30),  # 30 years old
        )
        profile = PlayerProfileFactory.create(
            user__userpreferences__localization=city_wwa,
        )
        api_client.force_authenticate(profile.user)
        url = reverse(
            url_profiles_near_me,
        )

        response = api_client.get(url, {"min_age": 18, "max_age": 25})

        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["uuid"] == str(g1.uuid)

        response = api_client.get(url, {"min_age": 18, "max_age": 32})

        assert response.status_code == 200
        assert response.data["count"] == 2

        response = api_client.get(url, {"min_age": 22, "max_age": 32})

        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["uuid"] == str(g2.uuid)
