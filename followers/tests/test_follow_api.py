from typing import Callable, Union
from uuid import UUID

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from parameterized import parameterized
from rest_framework.test import APITestCase

from followers.services import FollowServices
from labels.services import LabelService
from utils.factories import (
    CatalogFactory,
    ClubFactory,
    PlayerProfileFactory,
    TeamFactory,
)
from utils.factories.followers_factories import GenericFollowFactory
from utils.test.test_utils import UserManager

label_service = LabelService()
follow_service = FollowServices()


class TestFollowAPI(APITestCase):
    def setUp(self) -> None:
        self.user = UserManager(self.client)
        self.superuser = PlayerProfileFactory().user
        self.client.force_authenticate(user=self.superuser)

        self.profile = PlayerProfileFactory.create()
        self.team = TeamFactory.create()
        self.club = ClubFactory.create()
        self.catalog = CatalogFactory.create()

    def test_list_my_followers(self) -> None:
        """Test listing all followers of a user."""
        for _ in range(5):
            follow_service.follow_profile(
                self.superuser.profile.uuid, PlayerProfileFactory().user
            )

        response = self.client.get(reverse("api:followers:get_followers"))
        data = response.json()
        self.assertEqual(len(data), 5)
        self.assertEqual(response.status_code, 200)

    @parameterized.expand([
        ("profile", "profile_uuid", lambda self: self.profile.uuid),
        ("team", "team_id", lambda self: self.team.id),
        ("club", "club_id", lambda self: self.club.id),
        ("catalog", "catalog_slug", lambda self: self.catalog.slug),
    ])
    def test_follow_entity(
        self,
        entity_type: str,
        entity_id_field: str,
        get_entity_id: Callable[["TestFollowAPI"], Union[int, UUID]],
    ) -> None:
        """Test that a user can follow a profile, team, or club."""
        follow_url = reverse(
            f"api:followers:follow_{entity_type}",
            kwargs={entity_id_field: get_entity_id(self)},
        )
        response = self.client.post(follow_url)
        self.assertEqual(response.status_code, 201)

    @parameterized.expand([
        ("profile", "profile_uuid", lambda self: self.profile.uuid),
        ("team", "team_id", lambda self: self.team.id),
        ("club", "club_id", lambda self: self.club.id),
        ("catalog", "catalog_slug", lambda self: self.catalog.slug),
    ])
    def test_unfollow_entity(
        self,
        entity_type: str,
        entity_id_field: str,
        get_entity_id: Callable[["TestFollowAPI"], Union[int, UUID]],
    ) -> None:
        """Test that a user can unfollow a previously followed profile, team, or club."""
        follow_url = reverse(
            f"api:followers:follow_{entity_type}",
            kwargs={entity_id_field: get_entity_id(self)},
        )
        self.client.post(follow_url)

        unfollow_url = reverse(
            f"api:followers:unfollow_{entity_type}",
            kwargs={entity_id_field: get_entity_id(self)},
        )
        response = self.client.delete(unfollow_url)
        self.assertEqual(response.status_code, 204)

    def test_list_followed_objects(self) -> None:
        """Test listing all objects (profiles and teams) followed by a user."""
        GenericFollowFactory.create(
            user=self.superuser,
            object_id=self.profile.user.id,
            content_type=ContentType.objects.get_for_model(self.profile),
        )
        GenericFollowFactory.create(
            user=self.superuser,
            object_id=self.team.id,
            content_type=ContentType.objects.get_for_model(self.team),
        )
        response = self.client.get(reverse("api:followers:get_user_follows"))
        self.assertEqual(response.status_code, 200)

    @parameterized.expand([
        ("profile", "profile_uuid", lambda self: self.profile.uuid),
        ("team", "team_id", lambda self: self.team.id),
        ("club", "club_id", lambda self: self.club.id),
        ("catalog", "catalog_slug", lambda self: self.catalog.slug),
    ])
    def test_follow_entity_unauthenticated(
        self,
        entity_type: str,
        entity_id_field: str,
        get_entity_id: Callable[["TestFollowAPI"], Union[int, UUID]],
    ) -> None:
        """Test that unauthenticated users cannot follow a profile, team, or club."""
        self.client.logout()
        follow_url = reverse(
            f"api:followers:follow_{entity_type}",
            kwargs={entity_id_field: get_entity_id(self)},
        )
        response = self.client.post(follow_url)
        self.assertEqual(response.status_code, 401)

    @parameterized.expand([
        ("profile", "profile_uuid", lambda self: self.profile.uuid),
        ("team", "team_id", lambda self: self.team.id),
        ("club", "club_id", lambda self: self.club.id),
        ("catalog", "catalog_slug", lambda self: self.catalog.slug),
    ])
    def test_follow_entity_twice(
        self,
        entity_type: str,
        entity_id_field: str,
        get_entity_id: Callable[["TestFollowAPI"], Union[int, UUID]],
    ) -> None:
        """
        Test that a user cannot follow the same profile, team, club, or catalog twice.
        """
        follow_url = reverse(
            f"api:followers:follow_{entity_type}",
            kwargs={entity_id_field: get_entity_id(self)},
        )

        # First follow attempt
        response = self.client.post(follow_url)
        assert response.status_code == 201

        # Second follow attempt should result in an error
        response = self.client.post(follow_url)
        assert response.status_code == 400
