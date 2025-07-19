import uuid

from django.db.models import (
    ObjectDoesNotExist,
    QuerySet,
)
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response

from api.base_view import EndpointViewWithFilter
from api.consts import ChoicesTuple
from api.pagination import TransferRequestCataloguePagePagination
from api.serializers import ProfileEnumChoicesSerializer
from api.views import EndpointView
from clubs.services import LeagueService
from profiles.api import errors as api_errors
from profiles.api.errors import (
    PermissionDeniedHTTPException,
    TransferRequestDoesNotExistHTTPException,
    TransferStatusDoesNotExistHTTPException,
)
from profiles.api.filters import TransferRequestCatalogueFilter
from profiles.api.managers import SerializersManager
from profiles.serializers_detailed.base_serializers import (
    ProfileTransferRequestSerializer,
    TeamContributorSerializer,
)
from profiles.serializers_detailed.catalogue_serializers import (
    TransferRequestCatalogueSerializer,
)
from profiles.services import ProfileService, TeamContributorService
from roles.definitions import (
    TRANSFER_BENEFITS_CHOICES,
    TRANSFER_REQUEST_STATUS_CHOICES,
    TRANSFER_SALARY_CHOICES,
    TRANSFER_STATUS_ADDITIONAL_INFO_CHOICES,
    TRANSFER_STATUS_CHOICES_WITH_UNDEFINED,
    TRANSFER_TRAININGS_CHOICES,
)
from transfers.api.serializers import (
    ProfileTransferStatusSerializer,
    UpdateOrCreateProfileTransferSerializer,
)
from transfers.models import ProfileTransferRequest

profile_service = ProfileService()
team_contributor_service = TeamContributorService()


class TransferStatusAPIView(EndpointView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    league_service = LeagueService()

    def list_transfer_status(self, request: Request) -> Response:  # noqa
        """Retrieve and display transfer statuses for the profiles."""
        transfer_choices = (
            ChoicesTuple(*transfer)
            for transfer in TRANSFER_STATUS_CHOICES_WITH_UNDEFINED
        )
        serializer = ProfileEnumChoicesSerializer(transfer_choices, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_profile_transfer_status(
        self,
        request: Request,
        profile_uuid: uuid.UUID,  # noqa
    ) -> Response:
        """Retrieve and display transfer status for the user."""
        try:
            profile = profile_service.get_profile_by_uuid(profile_uuid)
        except ObjectDoesNotExist as exc:
            raise api_errors.ProfileDoesNotExist from exc
        transfer_status = profile.meta.transfer_object
        if not transfer_status:
            raise TransferStatusDoesNotExistHTTPException

        serializer = ProfileTransferStatusSerializer(
            transfer_status, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update_profile_transfer_status(  # noqa
        self, request: Request
    ) -> Response:
        """Update transfer status for the user."""
        profile = request.user.profile
        transfer_status = profile.meta.transfer_object

        if not transfer_status:
            raise api_errors.TransferStatusDoesNotExistHTTPException

        serializer = ProfileTransferStatusSerializer(
            instance=transfer_status,
            data=request.data,
            partial=True,
            context={"profile": profile, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    def create_profile_transfer_status(
        self,
        request: Request,
    ) -> Response:
        # views.py
        """Create transfer status for the profile."""
        profile = request.user.profile
        serializer = ProfileTransferStatusSerializer(
            data=request.data, context={"profile": profile, "request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_profile_transfer_status(
        self,
        request: Request,
    ) -> Response:
        """Delete transfer status for the profile."""
        profile = request.user.profile
        transfer_status = profile.meta.transfer_object

        if not transfer_status:
            raise api_errors.TransferStatusDoesNotExistHTTPException

        transfer_status.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_transfer_status_additional_info(self, request: Request) -> Response:  # noqa
        """Retrieve and display transfer statuses for the profiles."""
        transfer_status_additional_info_choices = (
            ChoicesTuple(*transfer)
            for transfer in TRANSFER_STATUS_ADDITIONAL_INFO_CHOICES
        )
        serializer = ProfileEnumChoicesSerializer(
            transfer_status_additional_info_choices, many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class TransferRequestAPIView(EndpointView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_manager = SerializersManager()

    def list_transfer_request_status(self, request: Request) -> Response:  # noqa
        """Retrieve and display transfer statuses for the profiles."""
        transfer_request_status_choices = (
            ChoicesTuple(*transfer) for transfer in TRANSFER_REQUEST_STATUS_CHOICES
        )
        serializer = ProfileEnumChoicesSerializer(
            transfer_request_status_choices, many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def list_transfer_request_number_of_trainings(
        self,
        request: Request,  # noqa
    ) -> Response:
        """
        Retrieve and display transfer status number of trainings for the profiles.
        """
        transfer_request_number_of_trainings_choices = (
            ChoicesTuple(*transfer) for transfer in TRANSFER_TRAININGS_CHOICES
        )
        serializer = ProfileEnumChoicesSerializer(
            transfer_request_number_of_trainings_choices, many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def list_transfer_request_benefits(
        self,
        request: Request,  # noqa
    ) -> Response:  # noqa
        """
        Retrieve and display transfer status additional information for the profiles.
        """
        transfer_request_additional_info_choices = (
            ChoicesTuple(*transfer) for transfer in TRANSFER_BENEFITS_CHOICES
        )
        serializer = ProfileEnumChoicesSerializer(
            transfer_request_additional_info_choices, many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def list_transfer_request_salary(self, request: Request) -> Response:  # noqa
        """
        Retrieve and display transfer status request salary for the profiles.
        """
        transfer_request_salary_choices = (
            ChoicesTuple(*transfer) for transfer in TRANSFER_SALARY_CHOICES
        )
        serializer = ProfileEnumChoicesSerializer(
            transfer_request_salary_choices, many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_profile_actual_teams(
        self, request: Request, profile_uuid: uuid.UUID
    ) -> Response:
        """
        Retrieve a list of team contributors associated
        with a given user profile and are actual ones. This endpoint is just
        for transfer request, so should be only visible for specific profile.
        """
        try:
            profile = profile_service.get_profile_by_uuid(profile_uuid)
        except ObjectDoesNotExist as exc:
            raise api_errors.ProfileDoesNotExist() from exc

        if profile.user != request.user:
            raise PermissionDeniedHTTPException

        queryset: QuerySet = team_contributor_service.get_profile_actual_teams(
            profile_uuid
        ).prefetch_related("team_history", "team_history__league_history__league")
        serializer = TeamContributorSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create_transfer_request(self, request: Request) -> Response:
        """Create transfer request for the profile."""
        profile = request.user.profile
        serializer = UpdateOrCreateProfileTransferSerializer(
            data=request.data, context={"profile": profile}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_profile_transfer_request(
        self,
        request: Request,
        profile_uuid: uuid.UUID,  # noqa
    ) -> Response:
        """Retrieve and display transfer request for the user."""
        try:
            profile = profile_service.get_profile_by_uuid(profile_uuid)
        except ObjectDoesNotExist as exc:
            raise api_errors.ProfileDoesNotExist() from exc
        transfer_request = profile.meta.transfer_object
        if not transfer_request:
            raise TransferRequestDoesNotExistHTTPException

        serializer = ProfileTransferRequestSerializer(
            transfer_request, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update_transfer_request(
        self,
        request: Request,
    ) -> Response:
        """Update transfer request for the user."""
        profile = request.user.profile
        transfer_request = profile.meta.transfer_object

        if not transfer_request:
            raise api_errors.TransferRequestDoesNotExistHTTPException

        serializer = UpdateOrCreateProfileTransferSerializer(
            instance=transfer_request,
            data=request.data,
            partial=True,
            context={"profile": profile},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete_profile_transfer_request(self, request: Request) -> Response:
        """Delete transfer request for the profile."""
        profile = request.user.profile
        transfer_request = profile.meta.transfer_object

        if not transfer_request:
            raise api_errors.TransferRequestDoesNotExistHTTPException

        transfer_request.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class TransferRequestCatalogueAPIView(EndpointViewWithFilter):
    permission_classes = [
        AllowAny,
    ]
    serializer_class = TransferRequestCatalogueSerializer
    pagination_class = TransferRequestCataloguePagePagination
    queryset = ProfileTransferRequest.objects.all().order_by("-created_at")
    filterset_class = TransferRequestCatalogueFilter

    # @method_decorator(cache_page(settings.DEFAULT_CACHE_LIFESPAN))
    def list_transfer_requests(self, request: Request) -> Response:
        """Retrieve and display transfer requests."""
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        paginated = self.get_paginated_queryset(queryset)
        serializer = self.serializer_class(
            paginated, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)
