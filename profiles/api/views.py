import logging
import random
import uuid
from datetime import timedelta
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.db.models import (
    Case,
    Count,
    IntegerField,
    ObjectDoesNotExist,
    QuerySet,
    When,
)
from django.utils import timezone
from rest_framework import exceptions, status
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import PermissionDenied

from api import utils as api_utils
from api.consts import ChoicesTuple
from api.errors import NotOwnerOfAnObject
from api.pagination import PagePagination, ProfileSearchPagination
from api.serializers import ProfileEnumChoicesSerializer
from api.views import EndpointView
from backend.settings import cfg
from external_links import serializers as external_links_serializers
from external_links.errors import LinkSourceNotFound, LinkSourceNotFoundServiceException
from external_links.services import ExternalLinksService
from labels.utils import fetch_all_labels
from profiles import errors, models
from profiles.api import errors as api_errors
from profiles.api import serializers
from profiles.api.managers import SerializersManager
from profiles.api.mixins import ProfileRetrieveMixin
from profiles.filters import ProfileListAPIFilter
from profiles.models import PROFILE_MODEL_MAP, ProfileMeta
from profiles.services import (
    ProfileFilterService,
    ProfileService,
    ProfileVideoService,
    ProfileVisitHistoryService,
    RandomizationService,
    TeamContributorService,
)
from profiles.utils import map_service_exception
from users.api.serializers import (
    MainUserDataSerializer,
    UserMainRoleSerializer,
    UserPreferencesUpdateSerializer,
)
from users.errors import UserPreferencesDoesNotExistHTTPException
from utils.cache import CachedResponse

if TYPE_CHECKING:
    pass

profile_service = ProfileService()
team_contributor_service = TeamContributorService()
external_links_services = ExternalLinksService()
User = get_user_model()
visit_history_service = ProfileVisitHistoryService()
randomization_service = RandomizationService()


logger = logging.getLogger(__name__)


# FIXME: lremkowicz: what about a django-filter library?
class ProfileAPI(ProfileListAPIFilter, EndpointView, ProfileRetrieveMixin):
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
        """GET single profile by uuid."""
        is_anonymous = api_utils.convert_bool(
            "is_anonymous", request.query_params.get("is_anonymous", "false")
        )
        try:
            profile_object = profile_service.get_profile_by_uuid(
                profile_uuid, is_anonymous
            )
        except ObjectDoesNotExist:
            raise api_errors.ProfileDoesNotExist

        if is_anonymous and not isinstance(profile_object, models.PlayerProfile):
            raise ValidationError("Only PlayerProfile can be anonymous.")

        return self.retrieve_profile_and_respond(request, profile_object)

    def get_profile_by_slug(self, request: Request, profile_slug: str) -> Response:
        """GET single profile by slug."""
        is_anonymous = profile_slug.startswith("anonymous-")
        try:
            if is_anonymous:
                anonymous_uuid = profile_slug.split("anonymous-")[-1]
                profile = ProfileService.get_anonymous_profile_by_uuid(anonymous_uuid)
            else:
                profile = profile_service.get_profile_by_slug(profile_slug)
                anonymous_uuid = None
        except ObjectDoesNotExist:
            raise api_errors.ProfileDoesNotExistBySlug

        if is_anonymous and not isinstance(profile, models.PlayerProfile):
            raise api_errors.ProfileDoesNotExist

        return self.retrieve_profile_and_respond(request, profile, is_anonymous, anonymous_uuid)

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
        # Get I18n-aware context from the mixin
        context = self.get_serializer_context()
        context.update({"requestor": request.user, "profile_uuid": profile_uuid})

        serializer = serializer_class(
            instance=profile,
            data=request.data,
            context=context,
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()

        return Response(serializer.data)

    def get_bulk_profiles(self, request: Request) -> Response:
        """
        Get list of profile for role delivered as param
        (?role={P, C, S, G, ...})
        Full list of choices can be found in roles/definitions.py
        """
        with CachedResponse(
            f"{cfg.redis.key_prefix.list_profiles}:{request.get_full_path()}", request
        ) as cache:
            if cached_data := cache.data:
                return Response(cached_data)

            qs: QuerySet = self.get_queryset()
            serializer_class = self.get_serializer_class(
                model_name=request.query_params.get("role")
            )
            if not serializer_class:
                serializer_class = serializers.ProfileSerializer

            paginated_query = self.paginate_queryset(qs)

            # Get I18n-aware context from the mixin
            context = self.get_serializer_context()
            context.update(
                {
                    "requestor": request.user,
                    "request": request,
                    "label_context": "base",
                    "premium_viewer": request.user.is_authenticated
                    and request.user.profile
                    and request.user.profile.is_premium,
                    "transfer_status": "1"
                    in self.query_params.get("transfer_status", []),
                }
            )

            serializer = serializer_class(
                paginated_query,
                context=context,
                many=True,
            )
            paginated_response = self.get_paginated_response(serializer.data)
            cache.data = paginated_response.data
            return paginated_response

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
        count = len(filtered_queryset)

        return Response({"count": count})

    def update_profile_contact(
        self, request: Request, profile_uuid: uuid.UUID
    ) -> Response:
        """User preferences contact update endpoint"""
        try:
            profile = profile_service.get_profile_by_uuid(profile_uuid)
        except ObjectDoesNotExist:
            raise api_errors.ProfileDoesNotExist
        except ValidationError:
            raise api_errors.InvalidUUID

        if profile.user != request.user:
            raise NotOwnerOfAnObject
        if not (user_preferences := request.user.userpreferences):
            raise UserPreferencesDoesNotExistHTTPException

        # Get I18n-aware context from the mixin
        context = self.get_serializer_context()
        context.update({"profile_uuid": profile_uuid})

        serializer = UserPreferencesUpdateSerializer(
            user_preferences,
            data=request.data,
            partial=True,
            context=context,
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()

        return Response(serializer.data)

    def get_main_user_data(self, request: Request, profile_uuid: uuid.UUID) -> Response:
        """Retrieve User main data"""
        try:
            profile = profile_service.get_profile_by_uuid(profile_uuid)
        except ObjectDoesNotExist:
            raise api_errors.ProfileDoesNotExist
        except ValidationError:
            raise api_errors.InvalidUUID

        if not profile.user.userpreferences:
            raise UserPreferencesDoesNotExistHTTPException

        serializer = MainUserDataSerializer(profile.user)

        return Response(serializer.data)

    def update_main_user_data(
        self, request: Request, profile_uuid: uuid.UUID
    ) -> Response:
        """User main data update endpoint"""
        try:
            profile = profile_service.get_profile_by_uuid(profile_uuid)
        except ObjectDoesNotExist:
            raise api_errors.ProfileDoesNotExist
        except ValidationError:
            raise api_errors.InvalidUUID

        if profile.user != request.user:
            raise NotOwnerOfAnObject
        if not request.user.userpreferences:
            raise UserPreferencesDoesNotExistHTTPException

        # Get I18n-aware context from the mixin
        context = self.get_serializer_context()

        serializer = MainUserDataSerializer(
            request.user,
            data=request.data,
            partial=True,
            context=context,
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()

        return Response(serializer.data)


class MixinProfilesFilter(ProfileListAPIFilter):
    PARAMS_PARSERS = {
        "latitude": api_utils.convert_float,
        "longitude": api_utils.convert_float,
        "radius": api_utils.convert_int,
        "min_age": api_utils.convert_int,
        "max_age": api_utils.convert_int,
        "role": api_utils.convert_str_list,
        "gender": api_utils.convert_str_list,
    }

    def filter_multiple_roles(self):
        """Filter queryset by multiple roles"""
        if roles := self.query_params.get("role", []):
            try:
                roles = [PROFILE_MODEL_MAP[role].__name__.lower() for role in roles]
            except KeyError:
                raise api_errors.InvalidProfileRole
            self.queryset = self.queryset.filter(_profile_class__in=roles)

    def filter_queryset(self) -> QuerySet:
        self.define_query_params()
        self.filter_multiple_roles()
        self.filter_localization()
        self.filter_age()
        self.filter_gender()
        return self.queryset


class PopularProfilesAPIView(MixinProfilesFilter, EndpointView):
    class Pagination(PagePagination):
        max_page_size = 10

    pagination_class = Pagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self) -> QuerySet:
        self.queryset = ProfileMeta.objects.annotate(
            visitors_count=Count("visited_objects")
        ).order_by("-visitors_count")
        self.filter_queryset()
        return self.queryset.distinct()

    def get_popular_profiles(self, request: Request) -> Response:
        """
        Retrieve popular profiles based on the specified filter criteria.

        This method processes a GET request containing various filter parameters
        and returns a list of popular profiles that match these filters.
        """
        user = request.user

        if int(request.query_params.get("page", 1)) > 1 and (
            not user.is_authenticated
            or (hasattr(user, "profile") and not user.profile.is_premium)
        ):
            return Response(status=status.HTTP_204_NO_CONTENT)

        with CachedResponse(
            cache_key=f"{cfg.redis.key_prefix.popular_profiles}:{request.get_full_path()}",
            request=request,
        ) as cache:
            if cached_data := cache.data:
                return Response(cached_data)

            qs = self.get_queryset()
            qs = self.paginate_queryset(qs)
            qs = [obj.profile for obj in qs]
            context = self.get_serializer_context()
            serializer = serializers.GenericProfileSerializer(
                qs, many=True, context=context
            )
            paginated_response = self.get_paginated_response(serializer.data)
            cache.data = paginated_response.data
            return paginated_response


class SuggestedProfilesAPIView(EndpointView):
    """
    API view for retrieving profiles similar to a specified profile based
    on certain criteria.

    This view applies a combination of Django filters and custom filtering logic to
    identify profiles similar to the given target profile.
    It supports different types of profiles like PlayerProfile and CoachProfile,
    applying specific filters based on the profile type.
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_suggested_profiles(
        self,
        request,
    ) -> Response:
        """
        Retrieves profiles suggested to the target profile specified by the UUID.
        """
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_204_NO_CONTENT)

        profile = user.profile
        params = {"user__last_activity__gte": timezone.now() - timedelta(days=30)}

        ordering = None
        if loc := user.userpreferences.localization:
            cities_nearby = profile_service.get_cities_nearby(loc)
            params["user__userpreferences__localization__in"] = cities_nearby
            city_id_order = list(cities_nearby.values_list("id", flat=True))
            ordering = Case(
                *[
                    When(user__userpreferences__localization__pk=cid, then=pos)
                    for pos, cid in enumerate(city_id_order)
                ],
                output_field=IntegerField(),
            )

        if profile.__class__ is models.PlayerProfile:
            qs_model = random.choice(
                [
                    models.CoachProfile,
                    models.ClubProfile,
                    models.ScoutProfile,
                ]
            )
        else:
            qs_model = models.PlayerProfile

        qs = qs_model.objects.to_list_by_api(
            **params,
        ).exclude(user__pk=user.pk)

        if ordering:
            qs = qs.annotate(city_order=ordering).order_by(
                "city_order", "-user__last_activity"
            )
        else:
            qs = qs.order_by("-user__last_activity")

        # Get I18n-aware context from the mixin
        context = self.get_serializer_context()

        serializer = serializers.SuggestedProfileSerializer(
            qs[:10], many=True, context=context
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProfilesNearbyAPIView(MixinProfilesFilter, EndpointView):
    class Pagination(PagePagination):
        max_page_size = 10

    pagination_class = Pagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    def filter_localization(self, *args, **kwargs) -> None:
        ...

    def get_profiles_nearby(self, request: Request) -> Response:
        """Retrieve profiles from the closest area"""
        user = request.user
        if not user.is_authenticated or not user.userpreferences.localization:
            return Response(status=status.HTTP_204_NO_CONTENT)

        if int(request.query_params.get("page", 1)) > 1 and (
            not user.is_authenticated
            or (hasattr(user, "profile") and not user.profile.is_premium)
        ):
            return Response(status=status.HTTP_204_NO_CONTENT)
        with CachedResponse(
            cache_key=f"user:{user.id}:{cfg.redis.key_prefix.profiles_nearby}:{request.get_full_path()}",
            request=request,
        ) as cache:
            if cached_data := cache.data:
                return Response(cached_data)

            cities_nearby = profile_service.get_cities_nearby(
                user.userpreferences.localization
            )
            city_id_order = list(cities_nearby.values_list("id", flat=True))
            ordering = Case(
                *[
                    When(user__userpreferences__localization__pk=cid, then=pos)
                    for pos, cid in enumerate(city_id_order)
                ],
                output_field=IntegerField(),
            )
            self.queryset = (
                ProfileMeta.objects.filter(
                    user__userpreferences__localization__in=cities_nearby,
                )
                .annotate(city_order=ordering)
                .exclude(user__pk=user.pk)
                .exclude(user__display_status=User.DisplayStatus.NOT_SHOWN)
                .order_by("city_order", "-user__last_activity")
            )
            qs = self.filter_queryset()
            paginated_qs = self.paginate_queryset(qs)

            # Get I18n-aware context from the mixin
            context = self.get_serializer_context()

            data = serializers.GenericProfileSerializer(
                paginated_qs, source="profile", many=True, context=context
            ).data
            paginated_response = self.get_paginated_response(data)
            cache.data = paginated_response.data
            return paginated_response


class ProfileSearchView(EndpointView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    allowed_methods = ["get"]
    pagination_class = ProfileSearchPagination

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

        context = self.get_serializer_context()

        serializer = serializers.ProfileSearchSerializer(
            paginated_profiles, many=True, context=context
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
        context = self.get_serializer_context()
        serializer = serializers.PlayerPositionSerializer(
            positions, many=True, context=context
        )
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
        context = self.get_serializer_context()
        serializer = ProfileEnumChoicesSerializer(
            labels_choices,
            many=True,  # type: ignore
            context=context,
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
        is_anonymous = api_utils.convert_bool(
            "is_anonymous", request.query_params.get("is_anonymous", "false")
        )

        # Retrieve the profile associated with the given UUID
        try:
            profile = profile_service.get_profile_by_uuid(profile_uuid, is_anonymous)
        except ObjectDoesNotExist:
            raise api_errors.ProfileDoesNotExist()

        profile_uuid = profile.uuid
        # Get sorted list of team contributors
        sorted_contributors: list = team_contributor_service.get_teams_for_profile(
            profile_uuid
        )
        # Using the manager to get the right serializer
        serializer_class = self.serializer_manager.get_serializer_class(
            profile, "output"
        )
        serializer = serializer_class(
            sorted_contributors,
            many=True,
            context={"request": request, "is_anonymous": is_anonymous},
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


class VisitationView(EndpointView):
    def list_my_visitors(self, request: Request) -> Response:
        """List visitors of the profile (premium Players and Guests only)."""
        if not hasattr(request.user, 'profile') or request.user.profile is None:
            return Response(
                {"detail": "Profile not found"}, status=status.HTTP_404_NOT_FOUND
            )
        
        profile = request.user.profile

        # Check if profile is premium
        if not profile.is_premium:
            return Response(
                {"detail": "Visitor statistics are only available for premium users"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if profile type is Player or Guest
        profile_type = profile.__class__.__name__
        if profile_type not in ["PlayerProfile", "GuestProfile"]:
            return Response(
                {"detail": "Visitor statistics are only available for players and guests"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get I18n-aware context from the mixin
        context = self.get_serializer_context()

        serializer = serializers.ProfileVisitSummarySerializer(profile, context=context)
        return Response(serializer.data, status=status.HTTP_200_OK)
