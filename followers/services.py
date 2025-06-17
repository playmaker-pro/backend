import uuid
from typing import Tuple

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import ObjectDoesNotExist

from clubs.errors import ClubNotFoundServiceException, TeamNotFoundServiceException
from clubs.models import Club, Team
from followers.errors import (
    AlreadyFollowingServiceException,
    FollowNotFoundServiceException,
    SelfFollowServiceException,
)
from followers.models import GenericFollow
from profiles.api import errors as api_errors
from profiles.models import Catalog
from profiles.services import ProfileService

User = get_user_model()

profile_service = ProfileService()


class FollowService:
    def _get_or_create_follow_instance(
        self, user: User, entity: models.Model, content_type: ContentType
    ) -> GenericFollow:
        """
        Helper method to create or get a follow instance.
        """
        follow_instance, created = GenericFollow.objects.get_or_create(
            user=user,
            object_id=entity.pk,
            content_type=content_type,
        )

        if not created:
            raise AlreadyFollowingServiceException

        return follow_instance

    def _get_content_type_for_model(self, model_class: models.Model) -> ContentType:
        """
        Helper method to get content type for a given model class.
        """
        return ContentType.objects.get_for_model(model_class)

    def get_follow_instance(
        self, user: User, entity_id: int, model_class
    ) -> GenericFollow:
        """
        Retrieves the follow relationship instance for a user and an entity.
        """
        content_type = self._get_content_type_for_model(model_class)
        try:
            follow_instance = GenericFollow.objects.get(
                user=user,
                object_id=entity_id,
                content_type=content_type,
            )
            return follow_instance
        except GenericFollow.DoesNotExist:
            raise FollowNotFoundServiceException

    @staticmethod
    def create_or_get_catalog(
        slug: str, name: str, description: str
    ) -> Tuple[Catalog, bool]:
        """
        Create or retrieve a catalog based on the given slug, name, and description.
        """
        return Catalog.objects.get_or_create(
            slug=slug, defaults={"name": name, "description": description}
        )

    def follow_profile(self, profile_uuid: uuid.UUID, user: User) -> GenericFollow:
        """
        Creates a follow relationship between a user and a profile.
        """
        try:
            profile = profile_service.get_profile_by_uuid(profile_uuid)
            if profile.user == user:
                raise SelfFollowServiceException

        except ObjectDoesNotExist:
            raise api_errors.ProfileDoesNotExist
        except ValidationError:
            raise api_errors.InvalidUUID

        content_type = self._get_content_type_for_model(profile.__class__)
        return self._get_or_create_follow_instance(user, profile, content_type)

    def follow_team(self, team_id: int, user: User) -> GenericFollow:
        """
        Creates a follow relationship between a user and a team.
        """
        try:
            team = Team.objects.get(id=team_id)
        except Team.DoesNotExist:
            raise TeamNotFoundServiceException

        content_type = self._get_content_type_for_model(team.__class__)
        return self._get_or_create_follow_instance(user, team, content_type)

    def follow_club(self, club_id: int, user: User) -> GenericFollow:
        """
        Creates a follow relationship between a user and a club.
        """
        try:
            club = Club.objects.get(id=club_id)
        except Club.DoesNotExist:
            raise ClubNotFoundServiceException("Club not found")

        content_type = self._get_content_type_for_model(club.__class__)
        return self._get_or_create_follow_instance(user, club, content_type)

    def follow_catalog(
        self,
        catalog_slug: str,
        user: User,
        name: str = "Unnamed Catalog",
        description: str = "",
    ) -> GenericFollow:
        """
        Creates a follow relationship between a user and a catalog.
        """
        # Create or retrieve the catalog based on the slug
        catalog, _ = self.create_or_get_catalog(
            slug=catalog_slug, name=f"{name} {catalog_slug}", description=description
        )

        content_type = self._get_content_type_for_model(catalog.__class__)
        return self._get_or_create_follow_instance(user, catalog, content_type)
