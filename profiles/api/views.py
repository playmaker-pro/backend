import logging
import uuid
from typing import Optional, Union

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.db.models import ObjectDoesNotExist, OuterRef, QuerySet, Subquery
from django.db.models.functions import Random
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import exceptions, status
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import PermissionDenied

from api.base_view import EndpointViewWithFilter
from api.consts import ChoicesTuple
from api.errors import NotOwnerOfAnObject
from api.pagination import TransferRequestCataloguePagePagination
from api.serializers import ProfileEnumChoicesSerializer
from api.swagger_schemas import (
    COACH_ROLES_API_SWAGGER_SCHEMA,
    FORMATION_CHOICES_VIEW_SWAGGER_SCHEMA,
)
from api.views import EndpointView
from clubs.models import Team
from clubs.services import LeagueService
from external_links import serializers as external_links_serializers
from external_links.errors import LinkSourceNotFound, LinkSourceNotFoundServiceException
from external_links.services import ExternalLinksService
from labels.utils import fetch_all_labels
from profiles import errors, models
from profiles.api import errors as api_errors
from profiles.api import serializers
from profiles.api.errors import (
    InvalidProfileRole,
    PermissionDeniedHTTPException,
    ProfileDoesNotExist,
    TransferRequestDoesNotExistHTTPException,
    TransferStatusDoesNotExistHTTPException,
)
from profiles.api.filters import PlayerProfileFilters, TransferRequestCatalogueFilter
from profiles.api.managers import SerializersManager
from profiles.errors import ProfileVisitHistoryDoesNotExistException
from profiles.filters import ProfileListAPIFilter
from profiles.interfaces import ProfileVisitHistoryProtocol
from profiles.models import PlayerProfile, ProfileTransferRequest
from profiles.serializers_detailed.base_serializers import (
    ProfileTransferRequestSerializer,
    ProfileTransferStatusSerializer,
    TeamContributorSerializer,
    UpdateOrCreateProfileTransferSerializer,
)
from profiles.serializers_detailed.catalogue_serializers import (
    TransferRequestCatalogueSerializer,
)
from profiles.services import (
    ProfileFilterService,
    ProfileService,
    ProfileVideoService,
    ProfileVisitHistoryService,
    TeamContributorService,
)
from profiles.utils import map_service_exception
from roles.definitions import (
    TRANSFER_BENEFITS_CHOICES,
    TRANSFER_REQUEST_STATUS_CHOICES,
    TRANSFER_SALARY_CHOICES,
    TRANSFER_STATUS_ADDITIONAL_INFO_CHOICES,
    TRANSFER_STATUS_CHOICES_WITH_UNDEFINED,
    TRANSFER_TRAININGS_CHOICES,
)
from users.api.serializers import UserMainRoleSerializer

profile_service = ProfileService()
team_contributor_service = TeamContributorService()
external_links_services = ExternalLinksService()
User = get_user_model()
visit_history_service = ProfileVisitHistoryService()


logger = logging.getLogger(__name__)


# FIXME: lremkowicz: what about a django-filter library?
class ProfileAPI(ProfileListAPIFilter, EndpointView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    allowed_methods = ["post", "patch", "get"]

    def create_profile(self, request: Request) -> Response:
        """Create initial profile for user"""
        serializer = serializers.CreateProfileSerializer(
            data=request.data, context={"requestor": request.user}
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_serializer_class(self, **kwargs):
        return SerializersManager().get_serializer(kwargs.get("model_name"))

    def get_profile_by_uuid(
        self, request: Request, profile_uuid: uuid.UUID
    ) -> Response:
        """GET single profile by uuid"""
        try:
            profile_object = profile_service.get_profile_by_uuid(profile_uuid)
        except ObjectDoesNotExist:
            raise api_errors.ProfileDoesNotExist

        # Profile visit counter
        if profile_object.user != request.user:
            requestor_profile: Union[models.BaseProfile, AnonymousUser] = request.user
            if request.user.is_authenticated:
                try:
                    requestor_profile = profile_service.get_profile_by_role_and_user(
                        user=request.user, role=request.user.role
                    )
                    if not requestor_profile:
                        raise ProfileDoesNotExist(details="Requestor has no profile")
                except ValueError:
                    raise InvalidProfileRole(details="Requestor has invalid role")

            history: ProfileVisitHistoryProtocol
            try:
                history = visit_history_service.get_user_profile_visit_history(
                    user=profile_object.user, created_at=timezone.now()
                )
                visit_history_service.increment(
                    instance=history, requestor=requestor_profile
                )

            except ProfileVisitHistoryDoesNotExistException:
                logger.error("Profile visit history does not exist. Creating one..")
                history = visit_history_service.create(user=profile_object.user)
                visit_history_service.increment(
                    instance=history, requestor=requestor_profile
                )

        serializer_class = self.get_serializer_class(
            model_name=profile_object.__class__.__name__
        )
        if not serializer_class:
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = serializer_class(
            profile_object, context={"request": request, "label_context": "profile"}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update_profile(self, request: Request, profile_uuid: uuid.UUID) -> Response:
        """PATCH request for profile (require UUID in body)"""

        try:
            profile = profile_service.get_profile_by_uuid(profile_uuid)
        except ObjectDoesNotExist:
            raise api_errors.ProfileDoesNotExist
        except ValidationError:
            raise api_errors.InvalidUUID

        if profile.user != request.user:
            raise NotOwnerOfAnObject

        serializer_class = self.get_serializer_class(
            model_name=f"{profile.__class__.__name__}_update"
        )
        if not serializer_class:
            serializer_class = serializers.UpdateProfileSerializer
        serializer = serializer_class(
            instance=profile,
            data=request.data,
            context={"requestor": request.user, "profile_uuid": profile_uuid},
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()

        return Response(serializer.data)

    def get_paginated_queryset(self, qs: QuerySet = None) -> Optional[list]:
        """Paginate queryset to optimize serialization"""
        qs: QuerySet = qs or self.get_queryset()
        return self.paginate_queryset(qs.order_by("data_fulfill_status"))

    def get_bulk_profiles(self, request: Request) -> Response:
        """
        Get list of profile for role delivered as param
        (?role={P, C, S, G, ...})
        Full list of choices can be found in roles/definitions.py
        """

        qs: QuerySet = self.get_queryset().order_by("data_fulfill_status", Random())

        serializer_class = self.get_serializer_class(
            model_name=request.query_params.get("role")
        )
        if not serializer_class:
            serializer_class = serializers.ProfileSerializer

        paginated_query = self.paginate_queryset(qs)
        serializer = serializer_class(
            paginated_query,
            context={"requestor": request.user, "label_context": "base"},
            many=True,
        )
        return self.get_paginated_response(serializer.data)

    def get_profile_labels(self, request: Request, profile_uuid: uuid.UUID) -> Response:
        try:
            profile_object = profile_service.get_profile_by_uuid(profile_uuid)
        except ObjectDoesNotExist:
            raise api_errors.ProfileDoesNotExist
        all_labels = fetch_all_labels(profile_object, label_context="profile")

        serializer = serializers.ProfileLabelsSerializer(all_labels, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_owned_profiles(self, request: Request) -> Response:
        """
        Get list of profiles owned by the current user
        [{uuid, role}, ...]
        """
        if isinstance(request.user, AnonymousUser):
            raise exceptions.NotAuthenticated

        profiles = profile_service.get_user_profiles(request.user)
        serializer = serializers.BaseProfileDataSerializer(profiles, many=True)
        return Response(serializer.data)

    def set_main_profile(self, request: Request) -> Response:
        """
        Set main profile for user
        """
        if not request.data.get("declared_role"):
            raise api_errors.IncompleteRequestBody(["declared_role"])
        serializer = UserMainRoleSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_filtered_profile_count(self, request: Request) -> Response:
        """
        Retrieve the count of profiles matching the specified filter criteria.

        This method processes a GET request containing various filter parameters
        and returns the count of profiles that match these filters, without
        actually fetching or returning the profile data. It's useful for getting
        a quick overview of how many profiles meet certain criteria before
        fetching the detailed data.

        The method works by extracting query parameters from the request,
        applying these filters to the queryset using ProfileListAPIFilter, and
        then counting the number of profiles in the filtered queryset.
        """
        # Extract and format query parameters
        query_params = {
            key: request.query_params.get(key) for key in request.query_params
        }

        # Instantiate ProfileListAPIFilter with formatted query parameters
        filter_service = ProfileListAPIFilter()
        filter_service.request = request
        filter_service.query_params = query_params  # Set the formatted query parameters

        # Apply the filters and get the filtered queryset
        filtered_queryset = filter_service.get_queryset()

        # Get the count of the filtered queryset
        count = filtered_queryset.count()

        return Response({"count": count})


class ProfileSearchView(EndpointView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    allowed_methods = ["get"]

    def get_paginated_queryset(self, qs: QuerySet = None) -> QuerySet:
        """Paginate queryset with custom page size"""
        self.pagination_class.page_size = 5
        return super().get_paginated_queryset(qs)

    def search_profiles(self, request: Request) -> Response:
        """
        Search for user profiles based on a provided search term.

        The search term is extracted from the "name" query parameter.
        If the term is not provided or is shorter than 3 characters,
        an InvalidSearchTerm exception is raised.
        Matching profiles are then retrieved and paginated.
        """
        search_term = request.GET.get("name", "").strip()

        try:
            matching_users_queryset = profile_service.search_profiles_by_name(
                search_term
            )
        except ValueError:
            raise api_errors.InvalidSearchTerm()
        paginated_profiles = self.get_paginated_queryset(matching_users_queryset)
        serializer = serializers.ProfileSearchSerializer(
            paginated_profiles, many=True, context={"request": request}
        )

        return self.get_paginated_response(serializer.data)


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
        roles = profile_service.get_club_roles_as_dict()
        return Response(roles, status=status.HTTP_200_OK)

    def get_referee_roles(self, request: Request) -> Response:
        """
        Get RefereeLevel roles and return response with format:
        [{id: id_name, name: role_name}, ...]
        """
        roles = (ChoicesTuple(*obj) for obj in profile_service.get_referee_roles())
        return Response(dict(roles), status=status.HTTP_200_OK)

    def get_player_age_range(self, request: Request) -> Response:
        """get players count group by age"""
        qs: QuerySet = ProfileFilterService.get_players_on_age_range()
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
        positions = models.PlayerPosition.objects.all()
        serializer = serializers.PlayerPositionSerializer(positions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CoachLicencesAPIView(EndpointView):
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

    def add_licence_for_coach(self, request: Request) -> Response:
        """
        Add licence for coach - POST request

        {
            "licence_id": 1,
            "expiry_date": "2025-03-19" (optional)
        }
        """
        serializer = serializers.CoachLicenceSerializer(
            data=request.data, context={"requestor": request.user}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def modify_licence_for_coach(self, request: Request, licence_id: int) -> Response:
        """
        Modify licence for coach - PATCH request
        {
            "licence_id": 2,
            "expiry_date": "2025-11-11"
        }
        """
        try:
            licence = models.CoachLicence.objects.get(pk=licence_id)
        except models.CoachLicence.DoesNotExist:
            raise exceptions.NotFound(
                f"CoachLicence with licence_id: {licence_id} does not exist."
            )

        serializer = serializers.CoachLicenceSerializer(
            licence, data=request.data, context={"requestor": request.user}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete_licence_for_coach(self, request: Request, licence_id: int) -> Response:
        """Delete licence for coach - DELETE request"""
        try:
            licence = models.CoachLicence.objects.get(pk=licence_id)
        except models.CoachLicence.DoesNotExist:
            raise exceptions.NotFound(
                f"CoachLicence with licence_id: {licence_id} does not exist."
            )

        serializer = serializers.CoachLicenceSerializer(
            licence, context={"requestor": request.user}
        )
        serializer.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileVideoAPI(EndpointView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_labels(self, request: Request) -> Response:
        """List profile video labels"""
        role = request.query_params.get("role")
        try:
            labels = ProfileVideoService.get_labels(role)
        except ValueError:
            raise api_errors.IncorrectProfileRole
        labels_choices = (ChoicesTuple(*label) for label in labels)
        serializer = ProfileEnumChoicesSerializer(
            labels_choices, many=True  # type: ignore
        )  # noqa: 501
        return Response(serializer.data)

    def create_profile_video(self, request: Request) -> Response:
        """View for creating new profile videos"""
        serializer = serializers.ProfileVideoSerializer(
            data=request.data,
            context={"requestor": request.user},
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_profile_video(self, request: Request, video_id: int) -> Response:
        """View for deleting profile videos"""

        try:
            obj = ProfileVideoService.get_video_by_id(video_id)
        except models.ProfileVideo.DoesNotExist:
            raise exceptions.NotFound(
                f"ProfileVideo with ID: {video_id} does not exist."
            )

        serializer = serializers.ProfileVideoSerializer(
            obj, context={"requestor": request.user}
        )
        serializer.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def update_profile_video(self, request: Request, video_id: int) -> Response:
        """View for updating existing profile video"""
        try:
            obj = ProfileVideoService.get_video_by_id(video_id)
        except models.ProfileVideo.DoesNotExist:
            raise exceptions.NotFound(
                f"ProfileVideo with ID: {video_id} does not exist."
            )

        serializer: serializers.ProfileVideoSerializer = (
            serializers.ProfileVideoSerializer(
                obj, data=request.data, context={"requestor": request.user}
            )
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProfileCoursesAPI(EndpointView):
    serializer_class = serializers.CourseSerializer

    def create(self, request: Request) -> Response:
        """Create new course for user"""
        serializer = self.serializer_class(
            data=request.data,
            context={"requestor": request.user},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request: Request, course_id: int) -> Response:
        """Update course for user"""

        try:
            course = models.Course.objects.get(pk=course_id)
        except models.Course.DoesNotExist:
            raise exceptions.NotFound("Course with given ID does not exist.")

        serializer = self.serializer_class(
            course, data=request.data, context={"requestor": request.user}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request: Request, course_id: int) -> Response:
        """Update course for user"""

        try:
            course = models.Course.objects.get(pk=course_id)
        except models.Course.DoesNotExist:
            raise exceptions.NotFound("Course with given ID does not exist.")

        serializer = self.serializer_class(course, context={"requestor": request.user})
        serializer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileTeamsApi(EndpointView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_manager = SerializersManager()

    def get_profile_team_contributor(
        self, request: Request, profile_uuid: uuid.UUID
    ) -> Response:
        """
        Retrieve a list of team contributors associated
        with a given user profile.
        """
        # Retrieve the profile associated with the given UUID
        try:
            profile = profile_service.get_profile_by_uuid(profile_uuid)
        except ObjectDoesNotExist:
            raise api_errors.ProfileDoesNotExist()

        # Get sorted list of team contributors
        sorted_contributors: list = team_contributor_service.get_teams_for_profile(
            profile_uuid
        )
        # Using the manager to get the right serializer
        serializer_class = self.serializer_manager.get_serializer_class(
            profile, "output"
        )
        serializer = serializer_class(
            sorted_contributors, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def add_team_contributor_to_profile(
        self, request: Request, profile_uuid: uuid.UUID
    ) -> Response:
        """
        Assigns a team with a team history to the user's profile.
        """
        user: User = profile_service.get_user_by_uuid(profile_uuid)
        if user != request.user:
            raise PermissionDenied
        profile: models.PROFILE_MODELS = profile_service.get_profile_by_uuid(
            profile_uuid
        )
        profile_short_type = next(
            (
                key
                for key, value in models.PROFILE_MODEL_MAP.items()
                if isinstance(profile, value)
            ),
            None,
        )
        # Using the manager to get the input serializer
        input_serializer_class = self.serializer_manager.get_serializer_class(
            profile, "input"
        )

        serializer_data = input_serializer_class(
            data=request.data, context={"profile_short_type": profile_short_type}
        )
        serializer_data.is_valid(raise_exception=True)
        validated_data = serializer_data.validated_data
        try:
            profile_type = (
                "player"
                if profile_service.is_player_or_guest_profile(profile)
                else "non-player"
            )
            team_contributor = team_contributor_service.create_contributor(
                profile_uuid, validated_data, profile_type
            )
        except Exception as e:
            mapped_exception = map_service_exception(e)
            if mapped_exception:
                raise mapped_exception
            raise
        # Using the manager to get the output serializer
        output_serializer_class = self.serializer_manager.get_serializer_class(
            profile, "output"
        )
        serializer = output_serializer_class(
            team_contributor, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update_profile_team_contributor(
        self, request: Request, team_contributor_id: int, profile_uuid: uuid.UUID
    ) -> Response:
        """
        Update a team with a team history in the user's profile.
        """
        user: User = profile_service.get_user_by_uuid(profile_uuid)
        if user != request.user:
            raise PermissionDenied

        profile: models.PROFILE_MODELS = profile_service.get_profile_by_uuid(
            profile_uuid
        )
        try:
            team_contributor: models.TeamContributor = (
                team_contributor_service.get_team_contributor_or_404(
                    team_contributor_id
                )
            )
        except errors.TeamContributorNotFoundServiceException:
            raise api_errors.TeamContributorDoesNotExist()

        if not team_contributor_service.is_owner_of_team_contributor(
            profile_uuid, team_contributor
        ):
            raise PermissionDenied()

        profile_short_type = next(
            (
                key
                for key, value in models.PROFILE_MODEL_MAP.items()
                if isinstance(profile, value)
            ),
            None,
        )
        serializer_context = {
            "request": request,
            "profile_short_type": profile_short_type,
        }
        # Using the manager to get the input serializer
        input_serializer_class = self.serializer_manager.get_serializer_class(
            profile, "input"
        )
        serializer_data = input_serializer_class(
            instance=team_contributor,
            data=request.data,
            partial=True,
            context=serializer_context,
        )
        serializer_data.is_valid(raise_exception=True)
        validated_data = serializer_data.validated_data
        try:
            if profile_service.is_player_or_guest_profile(profile):
                updated_team_contributor = (
                    team_contributor_service.update_player_contributor(
                        profile_uuid, team_contributor, validated_data
                    )
                )
            else:  # non-player profiles
                updated_team_contributor = (
                    team_contributor_service.update_non_player_contributor(
                        profile_uuid, team_contributor, validated_data
                    )
                )
        except Exception as e:
            mapped_exception = map_service_exception(e)
            if mapped_exception:
                raise mapped_exception
            raise e

        # Using the manager to get the output serializer
        output_serializer_class = self.serializer_manager.get_serializer_class(
            profile, "output"
        )
        serializer = output_serializer_class(
            updated_team_contributor, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete_profile_team_contributor(
        self, request: Request, team_contributor_id: int, profile_uuid: uuid.UUID
    ) -> Response:
        """
        Delete a team with a team history from the user's profile.
        """
        user: User = profile_service.get_user_by_uuid(profile_uuid)
        if user != request.user:
            raise PermissionDenied
        try:
            team_contributor = team_contributor_service.get_team_contributor_or_404(
                team_contributor_id
            )
        except errors.TeamContributorNotFoundServiceException:
            raise api_errors.TeamContributorDoesNotExist()

        if not team_contributor_service.is_owner_of_team_contributor(
            profile_uuid, team_contributor
        ):
            raise PermissionDenied()

        team_contributor_service.delete_team_contributor(team_contributor)

        return Response(status=status.HTTP_204_NO_CONTENT)


class ExternalLinksAPI(EndpointView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = external_links_serializers.ExternalLinksSerializer

    def get_profile_external_links(
        self, request: Request, profile_uuid: uuid.UUID
    ) -> Response:
        """Retrieve and display external links for the user."""
        try:
            profile = profile_service.get_profile_by_uuid(profile_uuid)
        except ObjectDoesNotExist:
            raise api_errors.ProfileDoesNotExist
        external_links = profile.external_links
        serializer = external_links_serializers.ExternalLinksSerializer(external_links)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def set_or_update_external_links(
        self, request: Request, profile_uuid: uuid.UUID
    ) -> Response:
        """Set or update multiple external links from provided data."""
        links_data = request.data.get("links", [])
        try:
            profile = profile_service.get_profile_by_uuid(profile_uuid)
        except ObjectDoesNotExist:
            raise api_errors.ProfileDoesNotExist
        if profile.user != request.user:
            raise PermissionDenied
        try:
            (
                modified_links,
                was_any_link_created,
            ) = external_links_services.upsert_links_for_user(profile, links_data)
        except LinkSourceNotFoundServiceException as e:
            raise LinkSourceNotFound(source_name=e.source_name)
        serializer = external_links_serializers.ExternalLinksEntitySerializer(
            modified_links, many=True
        )

        # Determine the status code: if any link was newly created, return 201. Else, return 200. # noqa: E501
        status_code = (
            status.HTTP_201_CREATED if was_any_link_created else status.HTTP_200_OK
        )

        return Response(serializer.data, status=status_code)


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
        self, request: Request, profile_uuid: uuid.UUID  # noqa
    ) -> Response:
        """Retrieve and display transfer status for the user."""
        try:
            profile = profile_service.get_profile_by_uuid(profile_uuid)
        except ObjectDoesNotExist as exc:
            raise api_errors.ProfileDoesNotExist from exc
        transfer_status = profile_service.get_profile_transfer_status(profile)
        if not transfer_status:
            raise TransferStatusDoesNotExistHTTPException

        serializer = ProfileTransferStatusSerializer(transfer_status)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update_profile_transfer_status(  # noqa
        self, request: Request, profile_uuid: uuid.UUID
    ) -> Response:
        """Update transfer status for the user."""

        try:
            profile = profile_service.get_profile_by_uuid(profile_uuid)
        except ObjectDoesNotExist as exc:
            raise api_errors.ProfileDoesNotExist from exc

        if profile.user != request.user:
            raise PermissionDeniedHTTPException

        transfer_status = profile_service.get_profile_transfer_status(profile)

        if not transfer_status:
            raise api_errors.TransferStatusDoesNotExistHTTPException

        serializer = ProfileTransferStatusSerializer(
            instance=transfer_status, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    def create_profile_transfer_status(
        self, request: Request, profile_uuid: uuid.UUID  # noqa
    ) -> Response:
        # views.py
        """Create transfer status for the profile."""
        try:
            profile = profile_service.get_profile_by_uuid(profile_uuid)
        except ObjectDoesNotExist as exc:
            raise api_errors.ProfileDoesNotExist from exc

        if profile.user != request.user:
            raise PermissionDeniedHTTPException

        serializer = ProfileTransferStatusSerializer(
            data=request.data, context={"profile": profile}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_profile_transfer_status(
        self, request: Request, profile_uuid: uuid.UUID  # noqa
    ) -> Response:
        """Delete transfer status for the profile."""
        try:
            profile = profile_service.get_profile_by_uuid(profile_uuid)
        except ObjectDoesNotExist as exc:
            raise api_errors.ProfileDoesNotExist from exc

        if profile.user != request.user:
            raise PermissionDeniedHTTPException

        transfer_status = profile_service.get_profile_transfer_status(profile)

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
        self, request: Request  # noqa
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
        self, request: Request  # noqa
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

    def create_transfer_request(
        self, request: Request, profile_uuid: uuid.UUID
    ) -> Response:
        """Create transfer request for the profile."""

        try:
            profile = profile_service.get_profile_by_uuid(profile_uuid)
        except ObjectDoesNotExist as exc:
            raise api_errors.ProfileDoesNotExist() from exc

        if profile.user != request.user:
            raise PermissionDeniedHTTPException

        serializer = UpdateOrCreateProfileTransferSerializer(
            data=request.data, context={"profile": profile}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_profile_transfer_request(
        self, request: Request, profile_uuid: uuid.UUID  # noqa
    ) -> Response:
        """Retrieve and display transfer request for the user."""
        try:
            profile = profile_service.get_profile_by_uuid(profile_uuid)
        except ObjectDoesNotExist as exc:
            raise api_errors.ProfileDoesNotExist() from exc
        transfer_request = profile_service.get_profile_transfer_request(profile)
        if not transfer_request:
            raise TransferRequestDoesNotExistHTTPException

        serializer = ProfileTransferRequestSerializer(
            transfer_request, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update_transfer_request(
        self, request: Request, profile_uuid: uuid.UUID  # noqa
    ) -> Response:
        """Update transfer request for the user."""

        try:
            profile = profile_service.get_profile_by_uuid(profile_uuid)
        except ObjectDoesNotExist as exc:
            raise api_errors.ProfileDoesNotExist() from exc

        if profile.user != request.user:
            raise PermissionDeniedHTTPException

        transfer_request = profile_service.get_profile_transfer_request(profile)

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

    def delete_profile_transfer_request(
        self, request: Request, profile_uuid: uuid.UUID
    ) -> Response:
        """Delete transfer request for the profile."""
        try:
            profile = profile_service.get_profile_by_uuid(profile_uuid)
        except ObjectDoesNotExist as exc:
            raise api_errors.ProfileDoesNotExist() from exc

        if profile.user != request.user:
            raise PermissionDeniedHTTPException

        transfer_request = profile_service.get_profile_transfer_request(profile)

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

    def list_transfer_requests(self, request: Request) -> Response:
        """Retrieve and display transfer requests."""
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        paginated = self.get_paginated_queryset(queryset)
        serializer = self.serializer_class(
            paginated, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)
