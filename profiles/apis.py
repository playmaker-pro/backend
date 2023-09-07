import uuid

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.db.models import ObjectDoesNotExist
from drf_spectacular.utils import extend_schema
from rest_framework import exceptions, status
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response

from api.errors import NotOwnerOfAnObject
from api.swagger_schemas import (
    COACH_ROLES_API_SWAGGER_SCHEMA,
    FORMATION_CHOICES_VIEW_SWAGGER_SCHEMA,
)
from api.views import EndpointView
from profiles import api_serializers, errors, serializers
from profiles.api_serializers import *
from profiles.filters import ProfileListAPIFilter
from profiles.services import PlayerVideoService, ProfileService

profile_service = ProfileService()


class ProfileAPI(ProfileListAPIFilter, EndpointView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    allowed_methods = ["post", "patch", "get"]

    def create_profile(self, request: Request) -> Response:
        """Create initial profile for user"""
        serializer = CreateProfileSerializer(
            data=request.data, context={"requestor": request.user}
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_profile_by_uuid(
        self, request: Request, profile_uuid: uuid.UUID
    ) -> Response:
        """GET single profile by uuid"""
        try:
            profile_object = profile_service.get_profile_by_uuid(profile_uuid)
        except ObjectDoesNotExist:
            raise errors.ProfileDoesNotExist

        serializer: api_serializers.ProfileSerializer = (
            api_serializers.ProfileSerializer(profile_object)
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update_profile(self, request: Request) -> Response:
        """PATCH request for profile (require UUID in body)"""
        try:
            profile_uuid: str = request.data.pop("uuid")
        except KeyError:
            raise errors.IncompleteRequestBody(("uuid",))

        try:
            profile = profile_service.get_profile_by_uuid(profile_uuid)
        except ObjectDoesNotExist:
            raise errors.ProfileDoesNotExist
        except ValidationError:
            raise errors.InvalidUUID

        if profile.user != request.user:
            raise NotOwnerOfAnObject

        serializer = api_serializers.UpdateProfileSerializer(
            instance=profile, data=request.data, context={"requestor": request.user}
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()

        return Response(serializer.data)

    def get_bulk_profiles(self, request: Request) -> Response:
        """
        Get list of profile for role delivered as param
        (?role={P, C, S, G, ...})
        """
        qs: QuerySet = self.get_paginated_queryset()
        serializer = ProfileSerializer(qs, many=True)
        return self.get_paginated_response(serializer.data)

    def get_profile_labels(self, request: Request, profile_uuid: uuid.UUID) -> Response:
        profile_object = profile_service.get_profile_by_uuid(profile_uuid)
        season_name = request.GET.get("season_name")
        query = {}
        if season_name:
            query = {"season_name": season_name}
        serializer = api_serializers.ProfileLabelsSerializer(
            profile_object.labels.filter(**query), many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_owned_profiles(self, request: Request) -> Response:
        """
        Get list of profiles owned by the current user
        [{uuid, role}, ...]
        """
        if isinstance(request.user, AnonymousUser):
            raise exceptions.NotAuthenticated

        profiles = profile_service.get_user_profiles(request.user)
        serializer = api_serializers.BaseProfileDataSerializer(profiles, many=True)
        return Response(serializer.data)


class FormationChoicesView(EndpointView):
    """
    Endpoint for listing formation choices.

    This endpoint returns a dictionary where each key-value pair is a formation's unique string representation
    (like "4-4-2" or "4-3-3") mapped to its corresponding label.
    For example, it may return a response like {"4-4-2": "4-4-2", "4-3-3": "4-3-3"}.
    """  # noqa: E501

    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(**FORMATION_CHOICES_VIEW_SWAGGER_SCHEMA)
    def list_formations(self, request: Request) -> Response:
        """
        Returns a list of formation choices.
        """
        return Response(dict(models.FORMATION_CHOICES), status=status.HTTP_200_OK)


class ProfileEnumsAPI(EndpointView):
    permission_classes = [AllowAny]
    http_method_names = ("get",)

    def get_club_roles(self, request: Request) -> Response:
        """
        Get ClubProfile roles and return response with format:
        ["Prezes", "Dyrektor sportowy",...]
        """
        roles = dict(profile_service.get_club_roles())
        return Response(list(roles.values()), status=status.HTTP_200_OK)

    def get_referee_roles(self, request: Request) -> Response:
        """
        Get RefereeLevel roles and return response with format:
        [{id: id_name, name: role_name}, ...]
        """
        roles = (
            serializers.ChoicesTuple(*obj)
            for obj in profile_service.get_referee_roles()
        )
        serializer = serializers.ProfileEnumChoicesSerializer(  # type: ignore
            roles, many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_player_age_range(self, request: Request) -> Response:
        """get players count group by age"""
        qs: QuerySet = profile_service.get_players_on_age_range()
        serializer = serializers.PlayersGroupByAgeSerializer(qs)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CoachRolesChoicesView(EndpointView):
    """
    View for listing coach role choices.
    The response is a dictionary where each item is a key-value pair:
    [role code, role name]. For example: {"IC": "Pierwszy trener", "IIC": "Drugi trener", ...}.
    """  # noqa: E501

    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(**COACH_ROLES_API_SWAGGER_SCHEMA)
    def list_coach_roles(self, request: Request) -> Response:
        """
        Return a list of coach roles choices.
        """
        return Response(
            dict(models.CoachProfile.COACH_ROLE_CHOICES), status=status.HTTP_200_OK
        )


class PlayerPositionAPI(EndpointView):
    """
    API endpoint for retrieving player positions.

    This class provides methods for retrieving all player positions, ordered by ID.
    It requires JWT authentication and allows read-only access for unauthenticated users.
    """  # noqa: E501

    permission_classes = [IsAuthenticatedOrReadOnly]

    def list_positions(self, request: Request) -> Response:
        """
        Retrieve all player positions ordered by ID.
        """
        positions = models.PlayerPosition.objects.all().order_by("id")
        serializer = serializers.PlayerPositionSerializer(positions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CoachLicencesChoicesView(EndpointView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    """
    View for listing coach licence choices.
    The response is a list of dictionaries each containing licence ID and licence name.
    For example: [{"id": 1, "name": "UEFA PRO", "key": "PRO"}, {"id": 2, "name": "UEFA A", "key":"A"}, ...].
    """  # noqa: E501

    def list_coach_licences(self, request: Request) -> Response:
        """
        Return a list of coach licences choices.
        """
        licences = models.LicenceType.objects.all()
        serializer = serializers.LicenceTypeSerializer(licences, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PlayerVideoAPI(EndpointView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_labels(self, request: Request) -> Response:
        """List all player video labels"""
        labels = (
            serializers.ChoicesTuple(*obj)
            for obj in PlayerVideoService.get_player_video_labels()
        )
        serializer = serializers.ProfileEnumChoicesSerializer(labels, many=True)  # type: ignore
        return Response(serializer.data)

    def create_player_video(self, request: Request) -> Response:
        """View for creating new player videos"""
        serializer = serializers.PlayerVideoSerializer(
            data=request.data, context={"requestor": request.user}
        )

        if serializer.is_valid(raise_exception=True):
            serializer.save()
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.profile, status=status.HTTP_201_CREATED)

    def delete_player_video(
        self, request: Request, video_id: typing.Optional[int] = None
    ) -> Response:
        """View for deleting player videos"""
        if not video_id:
            raise exceptions.ValidationError({"error": "Missing video_id."})

        try:
            obj = PlayerVideoService.get_video_by_id(video_id)
        except models.PlayerVideo.DoesNotExist:
            raise exceptions.NotFound(
                f"PlayerVideo with ID: {video_id} does not exist."
            )

        serializer = serializers.PlayerVideoSerializer(
            obj, context={"requestor": request.user}
        )
        serializer.delete()

        return Response(serializer.profile, status=status.HTTP_200_OK)

    def update_player_video(self, request: Request) -> Response:
        """View for updating existing player video"""
        if video_id := request.data.get("id"):  # noqa: E999
            try:
                obj = PlayerVideoService.get_video_by_id(video_id)
            except models.PlayerVideo.DoesNotExist:
                raise exceptions.NotFound(
                    f"PlayerVideo with ID: {video_id} does not exist."
                )

            serializer: serializers.PlayerVideoSerializer = (
                serializers.PlayerVideoSerializer(
                    obj, data=request.data, context={"requestor": request.user}
                )
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.profile, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise errors.IncompleteRequestBody(("id",))
