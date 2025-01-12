from datetime import timedelta
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from profiles.models import BaseProfile, ProfileVisitation
from utils.factories import PlayerProfileFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def profile():
    yield PlayerProfileFactory.create()


@pytest.fixture
def subject():
    player = PlayerProfileFactory()
    return player.user


@pytest.fixture
def client(subject):
    yield APIClient()


@pytest.fixture
def timezone_now():
    with patch("django.utils.timezone.now", return_value=timezone.now()) as mock_now:
        yield mock_now


url = reverse("api:profiles:list_my_visitors")


def _visit_factory(subject: BaseProfile) -> ProfileVisitation:
    return ProfileVisitation.upsert(visited=subject, visitor=PlayerProfileFactory())


def test_who_visited_my_profile_freemium(client, subject):
    client.force_authenticate(user=subject)
    response = client.get(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_who_visited_my_profile(client, subject):
    client.force_authenticate(user=subject)
    current_year = timezone.now().year
    subject_profile = subject.profile
    subject_profile.premium_products.setup_premium_profile()
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "this_month_count": 0,
        "this_year_count": 0,
        "visits": [],
    }

    # 32 days ago - should not be displayed
    pv4 = _visit_factory(subject_profile)
    pv4.timestamp = timezone.now() - timedelta(days=32)
    pv4.save()

    # 15 days ago
    pv2 = _visit_factory(subject_profile)
    pv2.timestamp = timezone.now() - timedelta(days=15)
    pv2.save()

    # 3 days ago
    pv1 = _visit_factory(subject_profile)
    pv1.timestamp = timezone.now() - timedelta(days=3)
    pv1.save()

    # 30 days ago
    pv3 = _visit_factory(subject_profile)
    pv3.timestamp = timezone.now() - timedelta(days=30)
    pv3.save()

    response = client.get(url)
    data = response.json()

    assert sum(subject.profile.visitation._visitors_count_per_year.values()) == 4
    assert response.status_code == status.HTTP_200_OK
    assert data["this_month_count"] == 3
    assert data["this_year_count"] == len(
        [
            is_curr
            for is_curr in [pv1, pv2, pv3, pv4]
            if is_curr.timestamp > timezone.now() - timedelta(weeks=52)
        ]
    )
    assert data["visits"][0]["visitor"]["uuid"] == str(pv1.visitor.profile.uuid)
    assert data["visits"][0]["days_ago"] == 3
    assert data["visits"][1]["visitor"]["uuid"] == str(pv2.visitor.profile.uuid)
    assert data["visits"][1]["days_ago"] == 15
    assert data["visits"][2]["visitor"]["uuid"] == str(pv3.visitor.profile.uuid)
    assert data["visits"][2]["days_ago"] == 30

    # visitor via get profile url
    client.force_authenticate(user=pv4.visitor.profile.user)
    client.get(
        reverse(
            "api:profiles:get_or_update_profile",
            kwargs={"profile_uuid": str(subject_profile.uuid)},
        )
    )

    client.force_authenticate(user=subject)
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["this_month_count"] == 4


def test_counter_per_year(timezone_now, subject):
    profile = subject.profile
    current_year = timezone.now().year
    for _ in range(3):
        _visit_factory(profile)

    assert profile.visitation.visitors_count_this_year == 3
    assert profile.visitation._visitors_count_per_year == {str(current_year): 3}

    # 1 year later
    timezone_now.return_value += timedelta(days=365)
    _visit_factory(profile)
    current_year = timezone.now().year

    assert profile.visitation.visitors_count_this_year == 1
    assert profile.visitation._visitors_count_per_year == {
        str(current_year): 1,
        str(current_year - 1): 3,
    }
