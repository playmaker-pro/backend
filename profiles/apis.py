import uuid
from drf_spectacular.utils import extend_schema
from api.views import EndpointView
from api.swagger_schemas import (
    COACH_ROLES_API_SWAGGER_SCHEMA,
    FORMATION_CHOICES_VIEW_SWAGGER_SCHEMA,
)
from profiles.api_serializers import (
    CreateProfileSerializer,
    profiles_service,
    ProfileSerializer,
    UpdateProfileSerializer,
    PlayerPositionSerializer,
)
from profiles.models import CoachProfile, PlayerPosition
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticatedOrReadOnly


class ProfileAPI(EndpointView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]
    allowed_methods = ["post", "patch", "get"]

    def create_profile(self, request: Request) -> Response:
        """Create initial profile for user"""
        serializer = CreateProfileSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_profile_by_uuid(
        self, request: Request, profile_uuid: uuid.UUID
    ) -> Response:
        profile_object = profiles_service.get_profile_by_uuid(profile_uuid)
        serializer: ProfileSerializer = ProfileSerializer(profile_object)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update_profile(self, request: Request) -> Response:
        serializer = UpdateProfileSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()

        return Response(serializer.data)


class FormationChoicesView(EndpointView):
    """
    Endpoint for listing formation choices.

    This endpoint returns a dictionary where each key-value pair is a formation's unique string representation
    (like "4-4-2" or "4-3-3") mapped to its corresponding label.
    For example, it may return a response like {"4-4-2": "4-4-2", "4-3-3": "4-3-3"}.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(**FORMATION_CHOICES_VIEW_SWAGGER_SCHEMA)
    def list_formations(self, request: Request) -> Response:
        """
        Returns a list of formation choices.
        """
        return Response(dict(CoachProfile.FORMATION_CHOICES), status=status.HTTP_200_OK)


class CoachRolesChoicesView(EndpointView):
    """
    View for listing coach role choices.
    The response is a dictionary where each item is a key-value pair:
    [role code, role name]. For example: {"IC": "Pierwszy trener", "IIC": "Drugi trener", ...}.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(**COACH_ROLES_API_SWAGGER_SCHEMA)
    def list_coach_roles(self, request: Request) -> Response:
        """
        Return a list of coach roles choices.
        """
        return Response(
            dict(CoachProfile.COACH_ROLE_CHOICES), status=status.HTTP_200_OK
        )


class PlayerPositionAPI(EndpointView):
    """
    API endpoint for retrieving player positions.

    This class provides methods for retrieving all player positions, ordered by ID.
    It requires JWT authentication and allows read-only access for unauthenticated users.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def list_positions(self, request: Request) -> Response:
        """
        Retrieve all player positions ordered by ID.
        """
        positions = PlayerPosition.objects.all().order_by("id")
        serializer = PlayerPositionSerializer(positions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
