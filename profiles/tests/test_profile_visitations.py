from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from profiles.models import ProfileVisitation
from utils.factories import (
    PlayerProfileFactory,
)

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


url = reverse("api:profiles:list_my_visitors")


def test_who_visited_my_profile_freemium(client, subject):
    client.force_authenticate(user=subject)
    response = client.get(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_who_visited_my_profile(client, subject):
    client.force_authenticate(user=subject)
    subject_profile = subject.profile
    subject_profile.premium_products.setup_premium_profile()
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

    # 32 days ago - should not be displayed
    pv4 = ProfileVisitation.upsert(
        visited=subject_profile, visitor=PlayerProfileFactory()
    )
    pv4.timestamp = timezone.now() - timedelta(days=32)
    pv4.save()

    # 15 days ago
    pv2 = ProfileVisitation.upsert(
        visited=subject_profile, visitor=PlayerProfileFactory()
    )
    pv2.timestamp = timezone.now() - timedelta(days=15)
    pv2.save()

    # 3 days ago
    pv1 = ProfileVisitation.upsert(
        visited=subject_profile, visitor=PlayerProfileFactory()
    )
    pv1.timestamp = timezone.now() - timedelta(days=3)
    pv1.save()

    # 30 days ago
    pv3 = ProfileVisitation.upsert(
        visited=subject_profile, visitor=PlayerProfileFactory()
    )
    pv3.timestamp = timezone.now() - timedelta(days=30)
    pv3.save()

    response = client.get(url)
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(data) == 3
    assert data[0]["visitor"]["uuid"] == str(pv1.visitor.profile.uuid)
    assert data[0]["days_ago"] == 3
    assert data[1]["visitor"]["uuid"] == str(pv2.visitor.profile.uuid)
    assert data[1]["days_ago"] == 15
    assert data[2]["visitor"]["uuid"] == str(pv3.visitor.profile.uuid)
    assert data[2]["days_ago"] == 30

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
    assert len(response.json()) == 4
