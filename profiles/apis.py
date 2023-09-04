import uuid

from django.db.models import QuerySet, Case, When, Value, BooleanField
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response

from api.swagger_schemas import (
    COACH_ROLES_API_SWAGGER_SCHEMA,
    FORMATION_CHOICES_VIEW_SWAGGER_SCHEMA,
)
from api.views import EndpointView

from . import api_serializers, filters, models, serializers, services

profile_service = services.ProfileService()


class ProfileAPI(filters.ProfileListAPIFilter, EndpointView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    allowed_methods = ["post", "patch", "get"]

    def get_paginated_queryset(self) -> QuerySet:
        """Paginate queryset to optimize serialization"""
        qs: QuerySet = self.get_queryset()
        return self.paginate_queryset(qs)

    def create_profile(self, request: Request) -> Response:
        """Create initial profile for user"""
        serializer = api_serializers.CreateProfileSerializer(
            data=request.data, context={"requestor": request.user}
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_profile_by_uuid(
        self, request: Request, profile_uuid: uuid.UUID
    ) -> Response:
        profile_object = profile_service.get_profile_by_uuid(profile_uuid)
        serializer: api_serializers.ProfileSerializer = (
            api_serializers.ProfileSerializer(profile_object)
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update_profile(self, request: Request) -> Response:
        serializer = api_serializers.UpdateProfileSerializer(
            data=request.data, context={"requestor": request.user}
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
        serializer = api_serializers.ProfileSerializer(qs, many=True)
        return self.get_paginated_response(serializer.data)


class FormationChoicesView(EndpointView):
    """
    Endpoint for listing formation choices.

    This endpoint returns a dictionary where each key-value pair is a formation's unique string representation
    (like "4-4-2" or "4-3-3") mapped to its corresponding label.
    For example, it may return a response like {"4-4-2": "4-4-2", "4-3-3": "4-3-3"}.
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(**FORMATION_CHOICES_VIEW_SWAGGER_SCHEMA)
    def list_formations(self, request: Request) -> Response:
        """
        Returns a list of formation choices.
        """
        return Response(dict(models.FORMATION_CHOICES), status=status.HTTP_200_OK)


class ProfileEnumsAPI(EndpointView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_club_roles(self, request: Request) -> Response:
        """
        Get ClubProfile roles and return response with format:
        [{id: 1, name: Trener}, ...]
        """
        roles = (
            serializers.ChoicesTuple(*obj) for obj in profile_service.get_club_roles()
        )
        serializer = serializers.ProfileEnumChoicesSerializer(roles, many=True)  # type: ignore
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_referee_roles(self, request: Request) -> Response:
        """
        Get RefereeLevel roles and return response with format:
        [{id: id_name, name: role_name}, ...]
        """
        roles = (
            serializers.ChoicesTuple(*obj)
            for obj in profile_service.get_referee_roles()
        )
        serializer = serializers.ProfileEnumChoicesSerializer(roles, many=True)  # type: ignore
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
    """

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
    """

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
    """

    def list_coach_licences(self, request: Request) -> Response:
        """
        Return a list of coach licences choices.
        """
        licences = models.LicenceType.objects.all()
        serializer = serializers.LicenceTypeSerializer(licences, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
