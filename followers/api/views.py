import uuid

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from api.base_view import EndpointView
from clubs.errors import (
    ClubDoesNotExist,
    ClubNotFoundServiceException,
    TeamDoesNotExist,
    TeamNotFoundServiceException,
)
from clubs.models import Club, Team
from clubs.services import ClubService, TeamHistoryCreationService
from followers.api.serializers import FollowedListSerializer, FollowingListSerializer
from followers.errors import (
    AlreadyFollowingException,
    AlreadyFollowingServiceException,
    FollowDoesNotExist,
    FollowNotFoundServiceException,
    SelfFollowException,
    SelfFollowServiceException,
)
from followers.services import FollowService
from profiles.api.errors import PermissionDeniedHTTPException
from profiles.api.mixins import ProfileRetrieveMixin
from profiles.errors import CatalogDoesNotExist, CatalogNotFoundServiceException
from profiles.models import Catalog
from profiles.services import ProfileService

profile_service = ProfileService()
follow_service = FollowService()
club_service = ClubService()
team_service = TeamHistoryCreationService()


class FollowAPIView(EndpointView, ProfileRetrieveMixin):
    permission_classes = [IsAuthenticated]

    def list_followed_objects(self, request: Request) -> Response:
        """
        List all objects followed by the current user.
        """
        if profile := request.user.profile:
            data = FollowedListSerializer(
                profile.who_i_follow,
                many=True,
                context={
                    "request": request,
                    "premium_viewer": request.user.profile.is_premium,
                },
            ).data
        else:
            data = []
        return Response(data, status=status.HTTP_200_OK)

    def list_my_followers(self, request: Request) -> Response:
        """
        List all followers of the current user.
        """
        if profile := request.user.profile:
            data = FollowingListSerializer(
                profile.who_follows_me,
                many=True,
                context={
                    "request": request,
                    "premium_viewer": request.user.profile.is_premium,
                },
            ).data
        else:
            data = []

        return Response(data, status=status.HTTP_200_OK)

    def follow_profile(self, request: Request, profile_uuid: uuid.UUID) -> Response:
        """
        Follow a profile identified by its UUID.
        """
        user = request.user
        try:
            follow_service.follow_profile(profile_uuid, user)
            return Response(
                {"message": "Profile followed successfully"},
                status=status.HTTP_201_CREATED,
            )
        except SelfFollowServiceException:
            raise SelfFollowException
        except AlreadyFollowingServiceException:
            raise AlreadyFollowingException(entity_type="profile")

    def unfollow_profile(self, request, profile_uuid: uuid.UUID) -> Response:
        """
        Unfollow a profile identified by its UUID.
        """
        user = request.user
        try:
            profile = profile_service.get_profile_by_uuid(profile_uuid)
            follow_instance = follow_service.get_follow_instance(
                user, profile.pk, profile.__class__
            )

            if follow_instance.user != user:
                raise PermissionDeniedHTTPException

            follow_instance.delete()
            return Response(
                {"message": "Profile unfollowed successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except FollowNotFoundServiceException:
            raise FollowDoesNotExist

    def follow_team(self, request: Request, team_id: int) -> Response:
        """
        Follow a team identified by its ID.
        """
        user = request.user

        try:
            follow_service.follow_team(team_id, user)
            return Response(
                {"message": "Team followed successfully"},
                status=status.HTTP_201_CREATED,
            )
        except TeamNotFoundServiceException:
            raise TeamDoesNotExist
        except AlreadyFollowingServiceException:
            raise AlreadyFollowingException(entity_type="type")

    def unfollow_team(self, request, team_id: int) -> Response:
        """
        Unfollow a team identified by its ID.
        """
        user = request.user
        try:
            team = team_service.get_team_by_id(team_id)
            follow_instance = follow_service.get_follow_instance(user, team.id, Team)

            if follow_instance.user != user:
                raise PermissionDeniedHTTPException

            follow_instance.delete()
            return Response(
                {"message": "Team unfollowed successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except FollowNotFoundServiceException:
            raise FollowDoesNotExist

    def follow_club(self, request: Request, club_id: int) -> Response:
        """
        Follow a club identified by its ID.
        """
        user = request.user

        try:
            follow_service.follow_club(club_id, user)
            return Response(
                {"message": "Club followed successfully"},
                status=status.HTTP_201_CREATED,
            )
        except ClubNotFoundServiceException:
            raise ClubDoesNotExist
        except AlreadyFollowingServiceException:
            raise AlreadyFollowingException(entity_type="club")

    def unfollow_club(self, request, club_id: int) -> Response:
        """
        Unfollow a club identified by its ID.
        """
        user = request.user
        try:
            club = club_service.club_exist(club_id)
            follow_instance = follow_service.get_follow_instance(user, club.id, Club)

            if follow_instance.user != user:
                raise PermissionDeniedHTTPException

            follow_instance.delete()
            return Response(
                {"message": "Club unfollowed successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except FollowNotFoundServiceException:
            raise FollowDoesNotExist

    def follow_catalog(self, request: Request, catalog_slug: str) -> Response:
        """
        Follow a catalog identified by its slug.
        """
        user = request.user

        try:
            follow_service.follow_catalog(
                catalog_slug,
                user,
                request.data.get("name", ""),
                request.data.get("description", ""),
            )
            return Response(
                {"message": "Catalog followed successfully"},
                status=status.HTTP_201_CREATED,
            )
        except AlreadyFollowingServiceException:
            raise AlreadyFollowingException(entity_type="catalog")

    def unfollow_catalog(self, request, catalog_slug: str) -> Response:
        """
        Unfollow a catalog identified by its slug.
        """
        user = request.user

        try:
            catalog = profile_service.get_catalog_by_slug(catalog_slug)
            follow_instance = follow_service.get_follow_instance(
                user, catalog.id, Catalog
            )

            if follow_instance.user != user:
                raise PermissionDeniedHTTPException

            follow_instance.delete()
            return Response(
                {"message": "Catalog unfollowed successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except FollowNotFoundServiceException:
            raise FollowDoesNotExist

        except CatalogNotFoundServiceException:
            raise CatalogDoesNotExist
