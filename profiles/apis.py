import uuid
from api.views import EndpointView
from profiles.api_serializers import (
    CreateProfileSerializer,
    profiles_service,
    ProfileSerializer,
    UpdateProfileSerializer,
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import PlayerPosition


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


class PlayerPositionAPI(EndpointView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def list_positions(self, request: Request) -> Response:
        positions = PlayerPosition.objects.all().order_by("id")
        positions_list = [
            {"position_id": position.id, "position_name": position.name}
            for position in positions
        ]
        return Response(positions_list, status=status.HTTP_200_OK)
