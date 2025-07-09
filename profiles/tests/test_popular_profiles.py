from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from profiles.models import CoachProfile, GuestProfile, PlayerProfile, ProfileVisitation
from utils.factories.profiles_factories import (
    CoachProfileFactory,
    GuestProfileFactory,
    PlayerProfileFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def player_20yo() -> PlayerProfile:
    """Fixture to create a player with 20 years of experience."""
    return PlayerProfileFactory.create(
        user__userpreferences__birth_date=timezone.now() - timedelta(days=20 * 365)
    )


@pytest.fixture
def coach_from_wwa(city_wwa) -> CoachProfile:
    """Fixture to create a coach from WWA."""
    return CoachProfileFactory.create(
        user__userpreferences__localization=city_wwa,
        user__userpreferences__birth_date=timezone.now() - timedelta(days=40 * 365),
    )


@pytest.fixture
def guest_profile() -> GuestProfile:
    """Fixture to create a guest profile."""
    return GuestProfileFactory.create()


@pytest.fixture()
def setup_visits(
    player_20yo,
    coach_from_wwa,
    guest_profile,
):
    """Fixture to set up visits for the test."""
    for _ in range(1):
        ProfileVisitation.upsert(
            visitor=GuestProfileFactory.create(), visited=guest_profile
        )

    for _ in range(3):
        ProfileVisitation.upsert(
            visitor=PlayerProfileFactory.create(), visited=coach_from_wwa
        )

    for _ in range(5):
        ProfileVisitation.upsert(
            visitor=CoachProfileFactory.create(), visited=player_20yo
        )


class TestPopularProfilesAPI:
    url = reverse("api:profiles:get_popular_profiles")

    def test_popular_profiles(
        self, api_client, player_20yo, coach_from_wwa, guest_profile, setup_visits
    ):
        """Test the popular profiles endpoint."""
        response = api_client.get(self.url)
        data = response.json()["results"]

        assert response.status_code == 200
        assert response.json()["count"] == 12
        assert data[0]["uuid"] == str(player_20yo.uuid)
        assert data[1]["uuid"] == str(coach_from_wwa.uuid)
        assert data[2]["uuid"] == str(guest_profile.uuid)

    def test_popular_profiles_filter_age(
        self,
        api_client,
    ):
        """Test the popular profiles endpoint with age filter."""
        assert PlayerProfile.objects.count() == 0
        profile = PlayerProfileFactory.create(
            user__userpreferences__birth_date=timezone.now() - timedelta(days=20 * 365)
        )
        response = api_client.get(self.url, {"min_age": 18, "max_age": 21})
        data = response.json()["results"]

        assert response.status_code == 200
        assert response.json()["count"] == 1
        assert data[0]["uuid"] == str(profile.uuid)

    def test_popular_profiles_filter_localization(
        self,
        api_client,
        city_prsk,
        coach_from_wwa,
    ):
        """Test the popular profiles endpoint with localization filter."""
        response = api_client.get(
            self.url,
            {
                "longitude": city_prsk.longitude,
                "latitude": city_prsk.latitude,
                "radius": 30,
            },
        )
        data = response.json()["results"]

        assert response.status_code == 200
        assert response.json()["count"] == 1
        assert data[0]["uuid"] == str(coach_from_wwa.uuid)

    @pytest.mark.parametrize(
        "roles, expected_count",
        [(("P", "T"), 10), (("S",), 0), (("G",), 2), (("P", "T", "G"), 12)],
    )
    def test_popular_profiles_filter_roles(
        self, api_client, roles, expected_count, setup_visits
    ):
        """Test the popular profiles endpoint with roles filter."""
        response = api_client.get(self.url, {"role": roles})

        assert response.status_code == 200
        assert response.json()["count"] == expected_count
