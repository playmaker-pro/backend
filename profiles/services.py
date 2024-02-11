import datetime
import hashlib
import logging
import typing
import uuid
from dataclasses import dataclass, field
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import MultipleObjectsReturned
from django.db import IntegrityError, connection
from django.db import models as django_base_models
from django.db.models import (
    Case,
    IntegerField,
    Model,
    ObjectDoesNotExist,
    Q,
    QuerySet,
    Value,
    When,
)
from django.db.models import functions as django_base_functions
from pydantic import BaseModel

from api.consts import ChoicesTuple
from api.services import LocaleDataService
from clubs import models as clubs_models
from clubs import services as club_services
from clubs.models import Club as CClub
from clubs.models import Team as CTeam
from profiles import errors, models, utils
from profiles.api import errors as api_errors
from profiles.interfaces import ProfileVisitHistoryProtocol
from profiles.models import (
    REVERSED_MODEL_MAP,
    BaseProfile,
    LicenceType,
    PlayerPosition,
    ProfileTransferStatus,
)
from roles.definitions import (
    CLUB_ROLES,
    PROFILE_TYPE_MAP,
    TRANSFER_BENEFITS_CHOICES,
    TRANSFER_REQUEST_STATUS_CHOICES,
    TRANSFER_SALARY_CHOICES,
    TRANSFER_STATUS_CHOICES_WITH_UNDEFINED,
    TRANSFER_TRAININGS_CHOICES,
    PlayerPositions,
    PlayerPositionShortcutsEN,
    PlayerPositionShortcutsPL,
)
from utils import get_current_season

logger = logging.getLogger(__name__)
User = get_user_model()
locale_service = LocaleDataService()
club_services = club_services.TeamHistoryCreationService()


class PositionData(BaseModel):
    """
    Represents the data structure for a player's position.
    """

    player_position: int
    is_main: bool


class ProfileVerificationService:
    """Profile verification service which can manage verification
    process for user's profile"""

    def __init__(self, profile: models.BaseProfile) -> None:
        self.profile: models.BaseProfile = profile
        self.user: User = self.profile.user

    def verify(self) -> None:
        if not self.user.validate_last_name():
            self.user.unverify()
            self.user.save()
            logger.info(
                f"User {self.user} has invalid last_name "
                f"={self.user.last_name}. Minimum 2char needed."
            )
            return
        if self.user.is_player:
            self._verify_player()
        elif self.user.is_coach:
            self._verify_coach()
        elif self.user.is_club:
            self._verify_club()

    def update_verification_data(
        self, data: dict, requestor: User = None
    ) -> models.ProfileVerificationStatus:
        """using dict-like data we can create new verification object"""
        logger.debug("New verification recieved for %s", self.user)
        team: typing.Optional[clubs_models.Team] = None
        team_history: typing.Optional[clubs_models.TeamHistory] = None
        club: typing.Optional[clubs_models.Club] = None
        text: typing.Optional[str] = None

        if team_club_league_voivodeship_ver := data.get(  # noqa: E999
            "team_club_league_voivodeship_ver"
        ):
            text = team_club_league_voivodeship_ver
        if has_team := data.get("has_team"):
            if has_team == "tak mam klub":
                has_team = True
            else:
                has_team = False

        team_not_found = data.get("team_not_found")

        if data.get("team") and team_not_found is False:
            if self.user.is_club:
                club = data.get("team")
            else:
                team_history = data.get("team")
                team = team_history.team
        else:
            if self.user.is_club:
                club = data.get("team")
            else:
                team = None
                team_history = None

        if has_team is True:
            if team_not_found:
                team = None
                team_history = None
                club = None
            else:
                text = None

        if has_team is False:
            team = None
            team_history = None
            club = None

        set_by: User = requestor or User.get_system_user()
        new: models.ProfileVerificationStatus = (
            models.ProfileVerificationStatus.objects.create(
                owner=self.user,
                previous=self.profile.verification,
                has_team=has_team,
                team_not_found=team_not_found,
                club=club,
                team=team,
                team_history=team_history,
                text=text,
                set_by=set_by,
            )
        )
        self.profile.verification = new
        self.profile.save()
        return new

    def update_verification_status(
        self, status: str, verification: models.ProfileVerificationStatus = None
    ) -> None:
        verification: models.ProfileVerificationStatus = (
            self.profile.verification or verification
        )
        verification.status = status
        verification.save()

    def _verify_user(self) -> None:
        self.user.verify()
        self.user.save()

    def _verify_player(self) -> None:
        profile: models.BaseProfile = self.profile

        if profile.verification.has_team and profile.verification.team:
            profile.team_object = profile.verification.team
            profile.team_club_league_voivodeship_ver = None
            self._verify_user()

        elif (
            profile.verification.has_team is True
            and profile.verification.team_not_found is True
            and profile.verification.text
        ):
            profile.team_object = None
            profile.team_club_league_voivodeship_ver = profile.verification.text
            self._verify_user()

        elif profile.verification.has_team is False and not profile.verification.text:
            profile.team_object = None
            profile.team_club_league_voivodeship_ver = None
            self._verify_user()
        elif profile.verification.has_team is False and profile.verification.text:
            profile.team_club_league_voivodeship_ver = profile.verification.text
            profile.team_object = None
        profile.save()

    def _verify_coach(self) -> None:
        profile: models.BaseProfile = self.profile

        if profile.verification.has_team and profile.verification.team_history:
            profile.team_object = profile.verification.team
            profile.team_history_object = profile.verification.team_history
            profile.team_club_league_voivodeship_ver = None
            profile.save()

            # remove managment of a team
            if hasattr(profile.user, "managed_team"):
                managed_team_id = profile.user.managed_team.id
                team = CTeam.objects.get(id=managed_team_id)
                team.visible = False
                team.manager = None
                team.save()

            if not profile.team_object.manager:
                profile.team_object.manager = profile.user
                profile.team_object.visible = True
                profile.team_object.save()

            if hasattr(profile.user, "managed_club"):
                managed_club_id = profile.user.managed_club.id
                club = CClub.objects.get(id=managed_club_id)
                club.manager = None
                club.save()

            if club := profile.team_object.club:
                if not club.manager:
                    club.manager = profile.user
                    club.save()

            self._verify_user()

        elif (
            profile.verification.has_team is True
            and profile.verification.team_not_found is True
            and profile.verification.text
        ):
            profile.team_object = None
            profile.team_club_league_voivodeship_ver = profile.verification.text
            self._verify_user()

        elif profile.verification.has_team is False and not profile.verification.text:
            profile.team_object = None
            profile.team_history_object = None
            profile.team_club_league_voivodeship_ver = None
            self._verify_user()

        elif profile.verification.has_team is False and profile.verification.text:
            profile.team_object = None
            profile.team_history_object = None
            profile.team_club_league_voivodeship_ver = profile.verification.text

            self._verify_user()
        profile.save()

    def _verify_club(self) -> None:
        profile: models.BaseProfile = self.profile
        if profile.verification.has_team and profile.verification.club:
            profile.club_object = profile.verification.club
            profile.team_club_league_voivodeship_ver = None
            profile.save()

            for t in profile.verification.club.teams.all():
                t.visible = True
                t.save()

            if hasattr(profile.user, "managed_club"):
                managed_club_id = profile.user.managed_club.id
                clubb = CClub.objects.get(id=managed_club_id)
                clubb.manager = None
                clubb.save()

            if not profile.club_object.manager:
                profile.club_object.manager = profile.user
                profile.club_object.save()
            else:
                profile.club_object.editors.add(profile.user)
                profile.club_object.save()
            self._verify_user()

        if (
            profile.verification.has_team is True
            and profile.verification.team_not_found is True
            and profile.verification.text
        ):
            profile.team_club_league_voivodeship_ver = profile.verification.text
            profile.club_object = None
            if hasattr(profile.user, "managed_club"):
                managed_club_id = profile.user.managed_club.id
                clubb = CClub.objects.get(id=managed_club_id)
                clubb.manager = None
                clubb.save()

            profile.save()
            self._verify_user()

        elif profile.verification.has_team is False and not profile.verification.text:
            profile.club_object = None
            profile.team_club_league_voivodeship_ver = None
            self._verify_user()
        elif profile.verification.has_team is False and profile.verification.text:
            profile.club_object = None
            profile.team_club_league_voivodeship_ver = profile.verification.text
            if hasattr(profile.user, "managed_club"):
                managed_club_id = profile.user.managed_club.id
                clubb = CClub.objects.get(id=managed_club_id)
                clubb.manager = None
                clubb.save()

            profile.save()
            self._verify_user()
        # profile.save()


class ProfileService:
    @staticmethod
    def set_initial_verification(profile: models.PROFILE_TYPE) -> None:
        """set initial verification status object if not present"""
        if profile.verification is None:
            profile.verification = models.ProfileVerificationStatus.create_initial(
                profile.user
            )
            profile.save()

    @staticmethod
    def set_and_create_user_profile(user: User) -> models.PROFILE_TYPE:
        """get type of profile and create profile"""
        profile_model = models.PROFILE_MODEL_MAP.get(user.role, models.GuestProfile)
        profile, _ = profile_model.objects.get_or_create(user=user)
        if user.is_player:
            models.PlayerMetrics.objects.get_or_create(player=profile)

        return profile

    @staticmethod
    def create_profile_with_initial_data(
        profile_type: models.PROFILE_TYPE, data: dict
    ) -> models.PROFILE_TYPE:
        """Create profile based on type, save with initial data"""
        return profile_type.objects.create(**data)

    @staticmethod
    def get_model_by_role(role: str) -> models.PROFILE_TYPE:
        """Get and return type of profile based on role (i.e.: 'S', 'P', 'C')"""
        try:
            return models.PROFILE_MODEL_MAP[role]
        except KeyError:
            raise ValueError("Invalid role shortcut.")

    def get_profile_by_role_and_user(
        self, role: str, user: User
    ) -> typing.Optional[models.PROFILE_TYPE]:
        """Get and return profile based on role and user"""
        profile_type = self.get_model_by_role(role)
        try:
            return profile_type.objects.get(user=user)
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def get_role_by_model(model: typing.Type[models.PROFILE_TYPE]) -> str:
        """Get and return role shortcut based on profile type"""
        return models.REVERSED_MODEL_MAP[model]

    @staticmethod
    def get_profile_by_uuid(
        profile_uuid: typing.Union[uuid.UUID, str]
    ) -> models.PROFILE_TYPE:
        """
        Get profile object using uuid
        Need to iterate through each profile type
        Iterated object (PROFILE_MODEL_MAP) has to include each subclass of BaseProfile
        Raise ProfileDoesNotExist if no any profile with given uuid exist
        """
        for profile_type in models.PROFILE_MODEL_MAP.values():
            try:
                return profile_type.objects.get(uuid=profile_uuid)
            except profile_type.DoesNotExist:
                continue
        else:
            raise ObjectDoesNotExist

    @staticmethod
    def get_profile_by_slug(slug: str) -> models.PROFILE_TYPE:
        """
        Get profile object using slug.
        Iterate through each profile type.
        Iterated object (PROFILE_MODEL_MAP) should include each subclass of BaseProfile.
        Raise ProfileDoesNotExist if no profile with the given slug exists.
        """
        for profile_type in models.PROFILE_MODEL_MAP.values():
            try:
                return profile_type.objects.get(slug=slug)
            except profile_type.DoesNotExist:
                continue
        else:
            raise ObjectDoesNotExist

    @staticmethod
    def is_valid_uuid(value: str) -> bool:
        try:
            uuid_obj = uuid.UUID(value)
        except ValueError:
            return False
        return str(uuid_obj) == value

    @staticmethod
    def get_club_roles() -> tuple:
        """Get list of club roles from ClubProfile"""
        return CLUB_ROLES

    @staticmethod
    def get_club_roles_as_dict() -> dict:
        """Get list of club roles from ClubProfile as a dict"""
        return dict(CLUB_ROLES)

    @staticmethod
    def get_referee_roles() -> tuple:
        """Get referee roles from RefereeProfile"""
        return models.RefereeLevel.REFEREE_ROLE_CHOICES

    @staticmethod
    def get_user_profiles(user: User) -> typing.List[models.PROFILE_TYPE]:
        """Find all profiles for given user"""
        profiles: list = []
        for profile_type in models.PROFILE_MODELS:
            if profile := profile_type.objects.filter(user=user).first():
                profiles.append(profile)
        return profiles

    @classmethod
    def get_user_by_uuid(cls, profile_uuid: uuid.UUID) -> User:
        """Fetches a profile by its UUID."""
        return cls.get_profile_by_uuid(profile_uuid).user

    @staticmethod
    def search_profiles_by_name(search_term: str) -> django_base_models.QuerySet:
        """
        Search for users whose concatenated first name and last name
        match the given search term.
        The search is case-insensitive and space-insensitive
        """
        # Validate the search term
        if not search_term or len(search_term) < 3:
            raise ValueError("Search term must be at least 3 characters long.")
        search_term = utils.preprocess_search_term(search_term)

        # First, get users who have a declared role
        users_with_declared_role = User.objects.filter(
            Q(declared_role__isnull=False) | Q(historical_role__isnull=False)
        )
        # Then, apply the custom search term processing
        matching_users = filter(
            lambda user: search_term
            in utils.preprocess_search_term(
                (user.first_name or "") + " " + (user.last_name or "")
            )
            and user.should_be_listed,
            users_with_declared_role,
        )

        matching_user_ids = [user.id for user in matching_users]
        return User.objects.filter(id__in=matching_user_ids)

    @staticmethod
    def is_player_or_guest_profile(profile) -> bool:
        return type(profile).__name__.lower() in ["playerprofile", "guestprofile"]

    @staticmethod
    def get_related_type_from_profile(profile_instance: models.BaseProfile) -> str:
        """
        Get the related type string for a given profile instance.

        The function fetches the model class of the provided profile instance,
        translates it to a short definition using a predefined mapping, and
        then translates the short definition to a related type string.
        """
        # Get the model class of the profile
        profile_class = profile_instance.__class__

        # Find the short definition using the REVERSED_MODEL_MAP
        short_definition = REVERSED_MODEL_MAP.get(profile_class)

        # Translate the short definition to the related type string using
        # PROFILE_TYPE_MAP
        related_type = PROFILE_TYPE_MAP.get(short_definition)

        return related_type

    @staticmethod
    def get_profile_transfer_status(
        profile: models.BaseProfile,
    ) -> typing.Optional[ProfileTransferStatus]:
        """Get the transfer status of a given profile."""
        transfer_status: ProfileTransferStatus = profile.transfer_status_related.first()
        return transfer_status or None

    @staticmethod
    def get_profile_transfer_request(
        profile: models.BaseProfile,
    ) -> typing.Optional[ProfileTransferStatus]:
        """Get the transfer status of a given profile."""
        transfer_request: ProfileTransferStatus = profile.transfer_requests.first()
        return transfer_request or None


class ProfileFilterService:
    profile_service = ProfileService

    @staticmethod
    def filter_youth_players(
        queryset: django_base_models.QuerySet,
    ) -> django_base_models.QuerySet:
        """Filter profiles queryset to get profiles of youth users (under 21 yo)"""
        max_youth_birth_date = utils.get_past_date(years=21)
        return queryset.filter(
            user__userpreferences__birth_date__gte=max_youth_birth_date
        )

    @staticmethod
    def filter_min_age(
        queryset: django_base_models.QuerySet, age: int
    ) -> django_base_models.QuerySet:
        """Filter profile queryset with minimum user age"""
        min_birth_date = utils.get_past_date(years=age)
        return queryset.filter(user__userpreferences__birth_date__lte=min_birth_date)

    @staticmethod
    def filter_max_age(
        queryset: django_base_models.QuerySet, age: int
    ) -> django_base_models.QuerySet:
        """Filter profile queryset with maximum user age"""
        max_birth_date = utils.get_past_date(years=age + 1)
        return queryset.filter(user__userpreferences__birth_date__gte=max_birth_date)

    @staticmethod
    def filter_player_position(
        queryset: django_base_models.QuerySet, positions: list
    ) -> django_base_models.QuerySet:
        """Filter profile queryset with maximum user age"""
        return (
            queryset.filter(player_positions__player_position__shortcut__in=positions)
            .annotate(
                is_main_for_positions=django_base_models.Case(
                    django_base_models.When(
                        player_positions__player_position__shortcut__in=positions,
                        then=django_base_models.F("player_positions__is_main"),
                    ),
                    default=django_base_models.F("player_positions__is_main"),
                    output_field=django_base_models.BooleanField(),
                )
            )
            .order_by("-is_main_for_positions", "?")
        )

    @staticmethod
    def filter_qs_by_player_position_id(
        queryset: django_base_models.QuerySet, positions: typing.List[int]
    ) -> django_base_models.QuerySet:
        """Filter queryset by player position id."""
        return queryset.filter(player_positions__player_position_id__in=positions)

    @staticmethod
    def filter_league(
        queryset: django_base_models.QuerySet, league_ids: list
    ) -> django_base_models.QuerySet:
        """
        Filter a queryset of profiles based on their association with the specified
        league IDs.

        The method prioritizes profiles who are associated with the leagues in the
        current season. If a profile has been associated with one of the given leagues in
        the current season, they are included in the results.
        If they haven't been associated in the current season but have been in
        past seasons, they are also included. However, profiles with current season
        associations are prioritized over those with only past associations.
        """
        current_season = get_current_season()

        distinct_user_ids = (
            queryset.filter(team_object__league_history__league__in=league_ids)
            .annotate(
                is_current_season=Case(
                    When(
                        team_object__league_history__season__name=current_season,
                        then=Value(1),
                    ),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            )
            .order_by("user_id", "-is_current_season")
            .values_list("user_id", flat=True)
            .distinct()
        )

        return queryset.filter(user_id__in=distinct_user_ids)

    @staticmethod
    def filter_player_gender(
        queryset: django_base_models.QuerySet, gender: str
    ) -> django_base_models.QuerySet:
        """Filter player's queryset by gender"""
        return queryset.filter(user__userpreferences__gender__in=gender)

    @staticmethod
    def filter_localization(
        queryset: django_base_models.QuerySet,
        latitude: float,
        longitude: float,
        radius: int,
    ) -> django_base_models.QuerySet:
        """
        Filter queryset with objects within radius based on
        longitude, latitude and radius (radius distance from target).
        Function uses Haversine formula (distance between two points on a sphere)
        """
        earth_radius = 6371
        latitude = Decimal(latitude)
        longitude = Decimal(longitude)

        return queryset.annotate(
            distance=earth_radius
            * django_base_functions.ACos(
                django_base_functions.Cos(django_base_functions.Radians(latitude))
                * django_base_functions.Cos(
                    django_base_functions.Radians(
                        "user__userpreferences__localization__latitude"
                    )
                )
                * django_base_functions.Cos(
                    django_base_functions.Radians(
                        "user__userpreferences__localization__longitude"
                    )
                    - django_base_functions.Radians(longitude)
                )
                + django_base_functions.Sin(django_base_functions.Radians(latitude))
                * django_base_functions.Sin(
                    django_base_functions.Radians(
                        "user__userpreferences__localization__latitude"
                    )
                )
            )
        ).filter(distance__lt=radius)

    @staticmethod
    def filter_country(
        queryset: django_base_models.QuerySet, country: list
    ) -> django_base_models.QuerySet:
        """
        Validate each country code, then return queryset filtered by given countries
        """
        return queryset.filter(
            user__userpreferences__citizenship__overlap=[
                locale_service.validate_country_code(code) for code in country
            ]
        )

    @staticmethod
    def filter_language(
        queryset: django_base_models.QuerySet, language: list
    ) -> django_base_models.QuerySet:
        """Validate each language code, then return queryset filtered by given
        spoken languages"""
        return queryset.filter(
            user__userpreferences__spoken_languages__code__in=[
                locale_service.validate_language_code(code) for code in language
            ]
        )

    @staticmethod
    def get_players_on_age_range(
        min_age: int = 14, max_age: int = 44
    ) -> django_base_models.QuerySet:
        """Get queryset of players with age between given args"""
        player_max_age = utils.get_past_date(years=max_age)
        player_min_age = utils.get_past_date(years=min_age)
        return models.PlayerProfile.objects.filter(
            user__userpreferences__birth_date__lte=player_min_age,
            user__userpreferences__birth_date__gte=player_max_age,
        )

    @staticmethod
    def validate_licence_keys(licence_keys: typing.List[str]) -> None:
        """
        Validates whether the provided licence names exist in the available licence
        names.

        This function checks each name in the provided list of licence names against the
        list of available licence names obtained from the LicenceType model. If any name
        is not found in the available names, a ValueError is raised.
        """
        available_keys = LicenceType.get_available_licence_names()
        for name in licence_keys:
            if name not in available_keys:
                raise ValueError(f"Invalid licence name: {name}")

    @staticmethod
    def filter_transfer_status(
        queryset: django_base_models.QuerySet, statuses: list
    ) -> django_base_models.QuerySet:
        """
        Filter a queryset of profiles based on multiple transfer statuses.

        This method iterates over a list of transfer status identifiers and applies
        filters to the queryset. Profiles with a status matching any of the specified
        identifiers are included in the result. Additionally, a special status identifier "5"  # noqa 501
        is used to include profiles that do not have an associated TransferStatus object.  # noqa 501
        """
        condition = Q()
        for status in statuses:
            if status == "5":
                condition |= Q(transfer_status_related__isnull=True)
            else:
                condition |= Q(transfer_status_related__status=status)

        return queryset.filter(condition)

    @staticmethod
    def filter_by_transfer_status_league(
        queryset: QuerySet, league_ids: typing.List[int]
    ) -> QuerySet:
        """
        Filter the queryset based on the league IDs associated with the profile's transfer status.
        """
        return queryset.filter(transfer_status_related__league__id__in=league_ids)

    @staticmethod
    def filter_by_additional_info(
        queryset: QuerySet, info: typing.List[str]
    ) -> QuerySet:
        """
        Filter the queryset based on additional information associated with the profile's transfer status.
        """
        return queryset.filter(transfer_status_related__additional_info__overlap=info)

    @staticmethod
    def filter_by_number_of_trainings(queryset: QuerySet, trainings: str) -> QuerySet:
        """
        Filter the queryset based on the number of trainings specified in the profile's transfer status.
        """
        return queryset.filter(transfer_status_related__number_of_trainings=trainings)

    @staticmethod
    def filter_by_benefits(queryset: QuerySet, benefits: typing.List[str]) -> QuerySet:
        """
        Filter the queryset based on benefits associated with the profile's transfer status.
        """
        return queryset.filter(transfer_status_related__benefits__overlap=benefits)

    @staticmethod
    def filter_by_salary(queryset: QuerySet, salary: str) -> QuerySet:
        """
        Filter the queryset based on the salary specified in the profile's transfer status.
        """
        return queryset.filter(transfer_status_related__salary=salary)

    @staticmethod
    def filter_min_pm_score(queryset: QuerySet, min_score: int) -> QuerySet:
        """Filter profiles with a minimum PlayMaker Score"""
        return queryset.filter(playermetrics__pm_score__gte=min_score)

    @staticmethod
    def filter_max_pm_score(queryset: QuerySet, max_score: int) -> QuerySet:
        """Filter profiles with a maximum PlayMaker Score"""
        return queryset.filter(playermetrics__pm_score__lte=max_score)

    @staticmethod
    def filter_by_position(
        queryset: QuerySet, target_profile: models.PROFILE_MODELS
    ) -> QuerySet:
        """
        Filters a queryset of profiles by the main position of the target player profile.
        es"""
        try:
            # Attempt to get the single main position
            main_position = target_profile.player_positions.get(is_main=True)
            return queryset.filter(
                player_positions__player_position=main_position.player_position,
                player_positions__is_main=True,
            ).distinct()
        except MultipleObjectsReturned:
            # Handle the case where more than one main position is found
            logger.warning(
                f"Multiple main positions found for profile {target_profile.uuid}"
            )
            return queryset
        except ObjectDoesNotExist:
            # Handle the case where no main position is found
            return queryset

    @staticmethod
    def filter_by_coach_role(
        queryset: QuerySet, target_profile: models.PROFILE_MODELS
    ) -> QuerySet:
        if target_profile.coach_role:
            return queryset.filter(coach_role=target_profile.coach_role).distinct()
        return queryset

    @staticmethod
    def apply_custom_filters(
        queryset: QuerySet, target_profile: models.PROFILE_MODELS
    ) -> QuerySet:
        model = type(target_profile)

        # Exclude the target profile itself
        queryset = queryset.exclude(uuid=target_profile.uuid)

        # Apply filters based on profile type
        if isinstance(target_profile, models.PlayerProfile):
            queryset = ProfileFilterService.filter_by_position(queryset, target_profile)
        elif isinstance(target_profile, models.CoachProfile):
            queryset = ProfileFilterService.filter_by_coach_role(
                queryset, target_profile
            )

        # Relax criteria if fewer than 10 profiles
        if queryset.count() < 10:
            # Relax position or coach role filter
            queryset = (
                model.objects.filter(
                    user__userpreferences__gender=target_profile.user.userpreferences.gender
                )
                .exclude(uuid=target_profile.uuid)
                .distinct()
            )

            # If still fewer than 10, relax gender filter
            if queryset.count() < 10:
                queryset = model.objects.exclude(uuid=target_profile.uuid).distinct()

        return queryset


class PlayerProfilePositionService:
    def validate_positions(self, positions_data: typing.List[PositionData]) -> None:
        """
        Validates the given positions data.

        raises MultipleMainPositionError: If more than one main position is found.
        raises TooManyAlternatePositionsError: If more than two non-main positions
        are found.
        """
        main_positions_count = len([data for data in positions_data if data.is_main])
        non_main_positions_count = len(
            [data for data in positions_data if not data.is_main]
        )

        if main_positions_count > 1:
            raise api_errors.MultipleMainPositionError

        if non_main_positions_count > 2:
            raise api_errors.TooManyAlternatePositionsError

    def manage_positions(
        self, profile: models.PlayerProfile, positions_data: typing.List[PositionData]
    ) -> None:
        """
        Updates the player positions associated with the given profile.

        This method takes a player profile and a list of positions data. It separates
        the positions into main and non-main positions, counts the number of main and
        non-main positions in the provided data, and raises an error if there are more
        than one main or two non-main positions.

        It then iterates over the new positions' data. If a main position is new or has
        changed, it is created or updated accordingly. Non-main positions are also
        created or updated, but no more than two are allowed.

        If any positions from the original set are not in the new positions data, they
        are deleted.
        """
        # Validate that the provided positions data meets the necessary criteria.
        self.validate_positions(positions_data)

        # Get the current positions associated with the profile, indexed by their
        # player_position_id.
        current_positions = {
            position.player_position_id: position
            for position in profile.player_positions.all()
        }

        # Initialize lists to hold positions that need to be created and updated.
        positions_to_create = []
        positions_to_update = []
        # Initialize a set to hold the IDs of positions that should be retained
        # (i.e., not deleted).
        position_ids_to_keep = set()

        # Iterate over new positions
        for position_data in positions_data:
            player_position_id = position_data.player_position
            is_main = position_data.is_main

            # Handle main position
            if is_main:
                if player_position_id not in current_positions:
                    # If no main position exists, prepare to create it
                    positions_to_create.append(
                        models.PlayerProfilePosition(
                            player_profile=profile,
                            player_position_id=player_position_id,
                            is_main=True,
                        )
                    )
                elif current_positions[player_position_id].is_main != is_main:
                    # If main position has changed, prepare to update it
                    positions_to_update.append(
                        (current_positions[player_position_id], is_main)
                    )

            # Handle non-main positions
            else:
                if player_position_id not in current_positions:
                    # If no such non-main position exists, prepare to create it
                    positions_to_create.append(
                        models.PlayerProfilePosition(
                            player_profile=profile,
                            player_position_id=player_position_id,
                            is_main=False,
                        )
                    )
                elif current_positions[player_position_id].is_main != is_main:
                    # If non-main position has changed, prepare to update it
                    positions_to_update.append(
                        (current_positions[player_position_id], is_main)
                    )

            position_ids_to_keep.add(player_position_id)

        # Delete positions not in positions_data
        positions_to_delete = set(current_positions.keys()) - position_ids_to_keep
        for position_id in positions_to_delete:
            current_positions[position_id].delete()

        # Update positions
        for position, is_main in positions_to_update:
            position.is_main = is_main
            position.save()

        # Create positions
        for position in positions_to_create:
            try:
                position.save()
            except IntegrityError:
                logger.error("Error saving player position", exc_info=True)


@dataclass
class PlayerPositionService:
    """Service for handling player position operation."""

    model: Model = field(default=PlayerPosition)

    def get_initial_position_data(self) -> typing.List[typing.List[str]]:
        """Get initial position data from consts enum classes."""
        positions: list = PlayerPositions.values()
        shortcuts_en: list = PlayerPositionShortcutsEN.values()
        shortcuts_pl: list = PlayerPositionShortcutsPL.values()
        if len(positions) == len(shortcuts_en) == len(shortcuts_pl):
            return [positions, shortcuts_en, shortcuts_pl]
        raise ValueError("Enum data is not equal")

    def get_old_raw_names(self) -> typing.List[str]:
        """Get old position names."""
        old_names = [
            "Bramkarz",
            "Obrońca Środkowy",
            "Obrońca Lewy",
            "Obrońca Prawy",
            "Pomocnik Defensywny (6)",
            "Pomocnik Środkowy (8)",
            "Pomocnik Ofensywny (10)",
            "Lewy pomocnik",
            "Prawy pomocnik",
            "Napastnik",
            "Skrzydłowy",
        ]
        return old_names

    @staticmethod
    def score_raw_mapping() -> dict:
        """Return mapping of position names to score names"""
        return {
            "Bramkarz": "Bramkarz",
            "Lewy Obrońca": "Obrońca",
            "Prawy Obrońca": "Obrońca",
            "Środkowy Obrońca": "Obrońca",
            "Defensywny Pomocnik #6": "Defensywny pomocnik",
            "Środkowy Pomocnik #8": "Ofensywny pomocnik",
            "Ofensywny Pomocnik #10": "Ofensywny pomocnik",
            "Lewy Pomocnik": "Ofensywny pomocnik",
            "Prawy Pomocnik": "Ofensywny pomocnik",
            "Skrzydłowy": "Ofensywny pomocnik",
            "Napastnik": "Napastnik",
        }

    def get_zipped_position_data(self) -> typing.Optional[zip]:
        """Get zipped position data from consts enum classes."""
        if len(self.get_initial_position_data()[0]) == len(self.get_old_raw_names()):
            return zip(*self.get_initial_position_data(), self.get_old_raw_names())
        raise ValueError("Enum data is not equal")

    def get_position_by_names(
        self, old_name: str, new_name: str
    ) -> typing.Tuple[typing.Optional[Model], bool]:
        """
        Get position by old or new name. Returns tuple with position object and
        boolean value if position exists.
        """
        obj = self.model.objects.filter(Q(name=old_name) | Q(name=new_name))
        if obj.exists():
            return obj.first(), True
        return None, False

    def update_instance(self, instance, **kwargs):
        """Update instance with given kwargs"""
        for kwarg in kwargs:
            setattr(instance, kwarg, kwargs[kwarg])
        instance.save()

    def create(self, **kwargs):
        """Create instance with given kwargs"""
        return self.model.objects.create(**kwargs)

    def update_score_for_position(self) -> None:
        """
        Updates the score of a given position.

        The method fetches the position object based on the provided name and updates
        its score_position name.
        """
        positions = self.model.objects.all()
        for position in positions:
            position.score_position = self.score_raw_mapping().get(position.name)
            position.save()

    def start_position_cleanup_process(self):
        """
        Method to start position cleanup process. It is responsible for
        updating position names, shortcuts, filling score_position field.
        """
        position_data = self.get_zipped_position_data()
        for order_number, position_dt in enumerate(position_data, start=1):
            name, shortcut_en, shortcut_pl, old_name = position_dt
            pp_from_db: PlayerPosition
            exists: bool
            pp_from_db, exists = self.get_position_by_names(
                old_name=old_name, new_name=name
            )

            if exists:
                self.update_instance(
                    pp_from_db,
                    name=name,
                    shortcut=shortcut_en,
                    shortcut_pl=shortcut_pl,
                    ordering=order_number,
                )
                logger.info(f"Updated position: {pp_from_db.pk}")
            else:
                self.create(
                    name=name,
                    shortcut=shortcut_en,
                    shortcut_pl=shortcut_pl,
                    ordering=order_number,
                )
                logger.info(f"Created position: {name}")

    def all(self):
        """Return all positions from DB."""
        return self.model.objects.all()


class ProfileVideoService:
    @staticmethod
    def get_labels(role: str = None) -> tuple:
        """Get video labels based on role if given"""
        if role:
            profile = ProfileService.get_model_by_role(role)
            return profile.get_profile_video_labels()
        return models.ProfileVideo.LABELS

    @staticmethod
    def get_video_by_id(_id: int) -> models.ProfileVideo:
        """Get ProfileVideo object by id"""
        return models.ProfileVideo.objects.get(id=_id)  # type: ignore


class TeamContributorService:
    profile_service = ProfileService()

    @staticmethod
    def get_team_contributor_or_404(team_contributor_id: int) -> models.TeamContributor:
        """
        Retrieves a TeamContributor by its ID or raises a custom exception if not found.
        """
        try:
            return models.TeamContributor.objects.get(pk=team_contributor_id)
        except models.TeamContributor.DoesNotExist:
            raise errors.TeamContributorNotFoundServiceException()

    @staticmethod
    def is_owner_of_team_contributor(
        profile_uuid: uuid.UUID, team_contributor: models.TeamContributor
    ) -> bool:
        """
        Checks if a profile is the owner of a given TeamContributor.
        """
        return team_contributor.profile_uuid == profile_uuid

    def get_teams_for_profile(
        self, profile_uuid: uuid.UUID, **kwargs
    ) -> typing.List[models.TeamContributor]:
        """
        Fetches all the teams associated with a given profile and returns them
        as a list.
        The resulting list is sorted first by the 'is_primary' field in
        descending order, and then by the latest season associated with
        each team contributor's team history, also in descending order.
        """
        queryset = self.filter_team_contributor(
            profile_uuid=profile_uuid, **kwargs
        ).prefetch_related("team_history", "team_history__league_history__season")
        # Sort the queryset
        sorted_contributors = sorted(
            queryset,
            key=lambda x: (
                -x.is_primary,
                -self.get_latest_season(x),
            ),
        )
        return sorted_contributors

    @staticmethod
    def filter_team_contributor(**kwargs):
        """Filter team contributor by given kwargs"""
        return models.TeamContributor.objects.filter(**kwargs).order_by("id")

    def get_profile_actual_teams(
        self, profile_uuid: uuid.UUID
    ) -> django_base_models.QuerySet:
        """
        Fetches all the teams associated with a given profile, following the model's
        Meta ordering.
        """
        return self.filter_team_contributor(
            profile_uuid=profile_uuid, end_date__isnull=True
        )

    @staticmethod
    def get_latest_season(team_contributor):
        seasons = team_contributor.team_history.values_list(
            "league_history__season__name", flat=True
        )
        # Convert each season to a sortable integer (e.g., "2024/2023" to 2024)
        sortable_seasons = [int(season.split("/")[0]) for season in seasons if season]
        # Sort seasons in descending order and return the first (latest) one
        return max(sortable_seasons) if sortable_seasons else 0

    @staticmethod
    def create_or_get_team_contributor(
        profile_uuid: uuid.UUID, team: clubs_models.Team, **kwargs
    ) -> typing.Tuple[models.TeamContributor, bool]:
        """
        Create or retrieve a TeamContributor instance for a given profile
        and team history.
        """
        # TODO: kgarczewski: FUTURE ADDITION: Reference: PM 20-697[SPIKE]
        # criteria = {
        #     "profile_uuid": profile_uuid,
        #     "team_history__in": [team_history],
        #     **kwargs,
        # }
        #
        # existing_contributor = models.TeamContributor.objects.filter(**criteria).first()  # noqa: E501
        #
        # if existing_contributor:
        #     return existing_contributor, False

        creation_criteria = {
            "profile_uuid": profile_uuid,
            **kwargs,
        }
        team_contributor_instance = models.TeamContributor.objects.create(
            **creation_criteria
        )
        # except IntegrityError:
        #     raise errors.TeamContributorAlreadyExistServiceException

        team_contributor_instance.team_history.add(team)

        return team_contributor_instance, True

    def exists_contributor(self, filters: dict) -> bool:
        """
        Check if a TeamContributor instance exists based on provided filters.
        """
        return models.TeamContributor.objects.filter(**filters).exists()

    @staticmethod
    def handle_primary_contributor(
        team_contributor: models.TeamContributor,
        profile_uuid: uuid.UUID,
        is_primary: typing.Optional[bool] = None,
        season: typing.Optional[str] = None,
        round_val: typing.Optional[str] = None,
        profile_type: str = "player",
        is_primary_for_round: typing.Optional[bool] = False,
    ) -> None:
        """
        Handle setting is_primary attribute and checking for existing primary
        contributors.
        """
        if is_primary:
            if profile_type == "player":
                # Unset any existing primary contributors with the given profile
                models.TeamContributor.objects.filter(
                    profile_uuid=profile_uuid,
                    is_primary=True,
                ).exclude(id=team_contributor.id).update(is_primary=False)
                team_contributor.is_primary = True
            else:
                contributors_to_unset = models.TeamContributor.objects.filter(
                    profile_uuid=profile_uuid, is_primary=True
                ).exclude(id=team_contributor.id)
                contributors_to_unset.update(
                    is_primary=False, end_date=datetime.date.today()
                )
                team_contributor.is_primary = True
                team_contributor.end_date = None
        elif is_primary is False:
            team_contributor.is_primary = False

        # If is_primary_for_round is provided and it's True
        if is_primary_for_round:
            models.TeamContributor.objects.filter(
                profile_uuid=profile_uuid,
                team_history__league_history__season=season,
                is_primary_for_round=True,
                round=round_val,
            ).exclude(id=team_contributor.id).update(is_primary_for_round=False)
            team_contributor.is_primary_for_round = True

        # If is_primary_for_round is provided and it's False
        elif is_primary_for_round is False:
            team_contributor.is_primary_for_round = False

        team_contributor.save()

    @staticmethod
    def reset_or_update_custom_role(
        team_contributor: models.TeamContributor, data: typing.Dict[str, typing.Any]
    ) -> bool:
        """
        Resets or updates the custom role of a team contributor based on the provided
        data.

        If the team contributor's role is changing from 'Other' to a different role,
        the custom role is reset to None. If the role is changing to 'Other'
        and a non-None custom role is provided, it updates the custom role.
        """
        role_changing_from_other = (
            team_contributor.role in models.TeamContributor.get_other_roles()
            and data.get("role") not in models.TeamContributor.get_other_roles()
        )
        role_changing_to_other = (
            data.get("role") in models.TeamContributor.get_other_roles()
        )
        custom_role_provided = "custom_role" in data and data["custom_role"] is not None
        custom_role_updated = False

        if role_changing_from_other:
            # Reset custom_role to None if changing from 'Other' to a different role
            team_contributor.custom_role = None
            custom_role_updated = True
        elif role_changing_to_other and custom_role_provided:
            # Update custom_role only if changing to 'Other' and a non-None custom_role
            # is provided
            team_contributor.custom_role = data["custom_role"]
            custom_role_updated = True

        return custom_role_updated

    def delete_team_contributor(self, team_contributor: models.TeamContributor) -> None:
        """
        Delete a TeamContributor instance and update related profile fields
        if necessary.
        """
        # Check if the team contributor is primary
        is_primary: bool = team_contributor.is_primary
        profile_uuid: uuid.UUID = team_contributor.profile_uuid

        # Delete the team contributor
        team_contributor.delete()

        # If the deleted contributor was primary, unset the team fields in the profile
        if is_primary:
            profile_instance: models.PROFILE_MODELS = (
                self.profile_service.get_profile_by_uuid(profile_uuid)
            )
            if profile_instance:
                profile_instance.team_object = None
                profile_instance.team_history_object = None
                profile_instance.save()

    def unified_fetch_related_entities(
        self, data: dict, profile_uuid: uuid.UUID, profile_type: str
    ) -> typing.Tuple:
        """
        Fetch or create team, league, league history, and team history based on
        the profile type.
        """
        league_identifier: typing.Union[str, int] = data.get("league_identifier")
        country_code: str = data.get("country", "PL")
        user = self.profile_service.get_user_by_uuid(profile_uuid)
        team: clubs_models.Team = club_services.get_or_create(data, user, country_code)

        if profile_type == "player":  # Handling for player profiles
            season = data.get("season")
            league, league_history = club_services.create_or_get_league_and_history(
                league_identifier, country_code, season, user, data
            )
            team_history = club_services.create_or_get_team_history(
                team, league_history, user
            )
        else:  # Handling for non-player profiles
            start_date = data["start_date"]
            end_date = data.get("end_date")
            team_histories = club_services.create_or_get_team_history_date_based(
                start_date, end_date, team.id, league_identifier, country_code, user
            )
            league, league_history = club_services.create_or_get_league_and_history(
                league_identifier,
                country_code,
                team_histories[-1].league_history.season,
                user,
                data,
            )
            team_history = team_histories[-1]

        return (
            team,
            league,
            league_history,
            team_history,
            season if profile_type == "player" else None,
        )

    def update_profile_team_fields(
        self, profile_uuid: uuid.UUID, team_history: clubs_models.Team
    ) -> None:
        """
        Updates the team field (`team_object`)
        of a profile instance.
        """
        profile_instance: models.PROFILE_MODELS = (
            self.profile_service.get_profile_by_uuid(profile_uuid)
        )

        profile_instance.team_object = team_history

        profile_instance.save()

    def update_profile_with_current_team_history(
        self,
        profile_uuid: uuid.UUID,
        matched_team_histories: typing.List[clubs_models.Team],
    ) -> None:
        """
        Updates the profile's team fields with the most current team history.
        """
        if not matched_team_histories:
            return
        # Sort the matched_team_histories by season in descending order
        sorted_team_histories = sorted(
            matched_team_histories,
            key=lambda th: th.league_history.season.name,
            reverse=True,
        )

        # The first one in the sorted list is the most current team history
        current_team_history = sorted_team_histories[0]

        self.update_profile_team_fields(profile_uuid, current_team_history)

    def create_contributor(
        self,
        profile_uuid: uuid.UUID,
        data: dict,
        profile_type: str,
    ) -> models.TeamContributor:
        """
        Creates or fetches a team contributor based on the profile type provided.
        """
        if profile_type == "player":
            return self.create_or_fetch_contributor(profile_uuid, data, is_player=True)
        else:
            return self.create_or_fetch_contributor(profile_uuid, data, is_player=False)

    def create_or_fetch_contributor(
        self,
        profile_uuid: uuid.UUID,
        data: typing.Dict[str, typing.Union[str, int, list]],
        is_player: bool,
    ) -> models.TeamContributor:
        """
        Create a contributor, either a player or a non-player, based on the
        provided data and profile UUID.
        """
        # Common logic
        criteria = {}
        matched_team_histories = self.get_or_create_team_history(data, profile_uuid)
        # Player-specific logic
        if is_player:
            criteria["round"] = data.get("round")
            criteria["is_primary_for_round"] = data.get("is_primary_for_round", False)
            # TODO: kgarczewski: FUTURE ADDITION: Reference: PM 20-697[SPIKE]
            # existing_contributor: models.TeamContributor = (
            #     self.check_existing_contributor(
            #         {
            #             "profile_uuid": profile_uuid,
            #             "team_history__in": matched_team_histories,
            #             "round": data.get("round"),
            #             "is_primary_for_round": data.get("is_primary_for_round"),
            #         }
            #     )
            # )

        # Non-player specific logic
        else:
            criteria["role"] = data.get("role")
            criteria["start_date"] = data["start_date"]
            criteria["end_date"] = data.get("end_date", None)
            if (
                "custom_role" in data
                and data["role"] in models.TeamContributor.get_other_roles()
            ):
                criteria["custom_role"] = data["custom_role"]
            # existing_contributor = self.check_existing_contributor(
            #     {
            #         "profile_uuid": profile_uuid,
            #         "team_history__in": matched_team_histories,
            #         "role": data.get("role"),
            #         "start_date": data.get("start_date"),
            #     }
            # )
        # Check if existing contributor
        # if existing_contributor:
        #     raise errors.TeamContributorAlreadyExistServiceException()

        # Create or get the team contributor
        team_contributor, was_created = self.create_or_get_team_contributor(
            profile_uuid, matched_team_histories[0], **criteria
        )

        # if not was_created:
        #     raise errors.TeamContributorAlreadyExistServiceException()

        # Handle primary contributor logic
        team_contributor.team_history.set(matched_team_histories)
        self.handle_primary_contributor(
            team_contributor=team_contributor,
            profile_uuid=profile_uuid,
            is_primary=data.get("is_primary", False),
            season=team_contributor.team_history.all()[0].league_history.season,
            is_primary_for_round=data.get("is_primary_for_round"),
            profile_type="player" if is_player else "non-player",
            round_val=data.get("round"),
        )
        # Check if the team_contributor is primary and update profile fields
        if data.get("is_primary", team_contributor.is_primary):
            self.update_profile_with_current_team_history(
                profile_uuid, matched_team_histories
            )
            self.synchronize_profile_role(team_contributor, profile_uuid)
        return team_contributor

    def get_or_create_team_history(
        self, data: dict, profile_uuid: uuid.UUID
    ) -> typing.List[typing.Union[clubs_models.Team, typing.Any]]:
        """
        Retrieve or create a team history based on the provided data and profile UUID.
        """
        is_player = (
            "start_date" not in data
        )  # Using "start_date" as the distinguishing factor
        # If a team_history is provided, fetch it
        if "team_history" in data and data["team_history"]:
            team_history_instance, _ = self.fetch_related_data(data, profile_uuid)

            if not is_player:  # non-player scenario
                # Extract attributes from team_history_instance, for example:
                team_parameter = team_history_instance.name
                league_identifier = team_history_instance.league_history.league.id

                # Use these extracted values to call
                # create_or_get_team_history_date_based
                return club_services.create_or_get_team_history_date_based(
                    data.get("start_date"),
                    data.get("end_date"),
                    team_parameter,
                    league_identifier,
                    data.get("country", "PL"),
                    self.profile_service.get_user_by_uuid(profile_uuid),
                )
            else:
                return [team_history_instance]

        # If this is a player profile
        if is_player:
            _, _, _, team_history, season = self.fetch_related_data(
                data, profile_uuid, "player"
            )
            return [team_history]

        # If this is a non-player profile
        else:
            return club_services.create_or_get_team_history_date_based(
                data.get("start_date"),
                data.get("end_date", None),
                data["team_parameter"],
                data["league_identifier"],
                data.get(
                    "country", "PL"
                ),  # Defaulting to "PL" if country is not provided
                self.profile_service.get_user_by_uuid(profile_uuid),
            )

    def fetch_related_data(
        self,
        data: dict,
        profile_uuid: uuid.UUID,
        profile_type: typing.Optional[str] = None,
    ) -> typing.Tuple:
        """
        Fetch related data based on the provided input data and profile type.
        """
        if "team_history" in data and data["team_history"]:
            team_history_instance = (
                data["team_history"][0]
                if isinstance(data["team_history"], list)
                else data["team_history"]
            )
            return club_services.fetch_team_history_and_season(team_history_instance.id)
        elif profile_type:
            return self.unified_fetch_related_entities(data, profile_uuid, profile_type)

    def check_existing_contributor(
        self,
        filters: dict,
        exclude_id: typing.Optional[int] = None,
    ) -> models.TeamContributor:
        """
        Check if a TeamContributor instance exists based on provided filters
        """
        existing_contributor = models.TeamContributor.objects.filter(**filters)
        if exclude_id:
            existing_contributor = existing_contributor.exclude(id=exclude_id)
        return existing_contributor.first()

    def update_team_contributor(
        self,
        team_contributor: models.TeamContributor,
        data: dict,
        team_histories: typing.List[clubs_models.Team],
    ) -> None:
        """
        Update attributes of a TeamContributor instance based on provided data.
        """
        # Set the team history for the contributor
        team_contributor.team_history.set(team_histories)

        # Start with fields that are always updated
        fields_to_update = ["round", "role", "start_date", "end_date"]

        # Update custom role and check if it needs to be saved
        if self.reset_or_update_custom_role(team_contributor, data):
            fields_to_update.append("custom_role")

        # Update the fields from the data provided.
        for field_to_update in fields_to_update:
            if field_to_update in data and field_to_update != "custom_role":
                setattr(team_contributor, field_to_update, data[field_to_update])

        # Now save only the fields that were updated.
        team_contributor.save(update_fields=fields_to_update)
        if team_contributor.is_primary:
            self.synchronize_profile_role(
                team_contributor, team_contributor.profile_uuid
            )

    def update_player_contributor(
        self,
        profile_uuid: uuid.UUID,
        team_contributor: models.TeamContributor,
        data: dict,
    ) -> models.TeamContributor:
        """
        Update player contributor data.

        This function updates a player contributor by fetching the relevant team history
        based on the input data. It checks for any existing contributor that matches the
        provided criteria and raises an exception if one exists. If the contributor
        is marked as primary, the function handles the primary contributor logic.
        Finally, the function updates the team contributor instance with the
        new data provided.
        """
        team_history_instance = team_contributor.team_history.first()

        if team_history_instance:
            current_data = {
                "round": team_contributor.round,
                "team_parameter": team_history_instance.id,
                "league_identifier": team_history_instance.league_history.league.id,
                "season": team_history_instance.league_history.season.id,
                "is_primary": team_contributor.is_primary,
                "is_primary_for_round": team_contributor.is_primary_for_round,
            }
        current_data.update(data)
        profile_type = "player"
        if "team_history" in current_data and current_data.get("team_history"):
            team_history, season = self.fetch_related_data(
                current_data, profile_uuid, profile_type
            )
        else:
            team_history = club_services.create_or_get_team_history_for_player(
                current_data.get("season"),
                current_data.get("team_parameter"),
                current_data.get("league_identifier"),
                current_data.get("country", "PL"),
                self.profile_service.get_user_by_uuid(profile_uuid),
            )
        # TODO: kgarczewski: FUTURE ADDITION: Reference: PM 20-697[SPIKE]
        # existing_contributor: models.TeamContributor = self.check_existing_contributor(  # noqa: E501
        #     {
        #         "profile_uuid": profile_uuid,
        #         "team_history__in": [team_history],
        #         "round": data.get("round"),
        #     },
        #     team_contributor.pk,
        # )

        # if existing_contributor:
        #     raise errors.TeamContributorAlreadyExistServiceException()
        self.handle_primary_contributor(
            team_contributor,
            profile_uuid,
            current_data.get("is_primary"),
            current_data.get("season"),
            current_data.get("round"),
            profile_type,
            current_data.get("is_primary_for_round"),
        )
        self.update_team_contributor(team_contributor, data, [team_history])
        if data.get("is_primary", team_contributor.is_primary):
            self.update_profile_team_fields(profile_uuid, team_history)

        return team_contributor

    def update_non_player_contributor(
        self,
        profile_uuid: uuid.UUID,
        team_contributor: models.TeamContributor,
        data: dict,
    ) -> models.TeamContributor:
        """
        Update non-player contributor data.

        This function updates a non-player contributor by fetching or creating the
        relevant team history based on the input data. It then updates the team
        contributor instance with the new data provided.
        """
        team_history_instance = team_contributor.team_history.first()
        if team_history_instance:
            current_data = {
                "start_date": team_contributor.start_date,
                "end_date": team_contributor.end_date,
                "team_parameter": team_history_instance.id,
                "league_identifier": team_history_instance.league_history.league.id,
                "is_primary": team_contributor.is_primary,
                "role": team_contributor.role,
                "custom_role": team_contributor.custom_role,
            }
        current_data.update(data)

        if "team_history" in current_data and current_data.get("team_history"):
            team_history_instance, season = self.fetch_related_data(
                current_data, profile_uuid, None
            )
            matched_team_histories = [team_history_instance]
        else:
            matched_team_histories = (
                club_services.create_or_get_team_history_date_based(
                    current_data.get("start_date"),
                    current_data.get("end_date"),
                    current_data.get("team_parameter"),
                    current_data.get("league_identifier"),
                    current_data.get("country", "PL"),
                    self.profile_service.get_user_by_uuid(profile_uuid),
                )
            )
        # TODO: kgarczewski: FUTURE ADDITION: Reference: PM 20-697[SPIKE]
        # existing_contributor: models.TeamContributor = self.check_existing_contributor(  # noqa: E501
        #     {
        #         "profile_uuid": profile_uuid,
        #         "role": current_data.get("role"),
        #         "start_date": current_data.get("start_date"),
        #         "end_date": current_data.get("end_date"),
        #         "team_history__in": matched_team_histories,
        #     },
        #     team_contributor.pk,
        # )

        # if existing_contributor:
        #     raise errors.TeamContributorAlreadyExistServiceException()
        self.handle_primary_contributor(
            team_contributor,
            profile_uuid,
            current_data.get("is_primary", False),
            profile_type="nonplayerprofile",
        )
        self.update_team_contributor(
            team_contributor, current_data, matched_team_histories
        )
        if data.get("is_primary", team_contributor.is_primary):
            self.update_profile_with_current_team_history(
                profile_uuid, matched_team_histories
            )

        return team_contributor

    def synchronize_profile_role(
        self, team_contributor: models.TeamContributor, profile_uuid: uuid.UUID
    ) -> None:
        """
        Synchronizes the role or custom role from a TeamContributor instance to the
        corresponding profile.

        This method updates the role field in a profile based on the role or
        custom role specified in the TeamContributor instance.
        If the role in TeamContributor is marked as 'OTC' or 'O'
        (indicating a custom role), it updates the profile's custom role field
        ('custom_coach_role' or 'custom_club_role'). Otherwise, it updates the
        standard role field ('coach_role' or 'club_role').
        """
        profile = self.profile_service.get_profile_by_uuid(profile_uuid)

        if team_contributor.role in ["OTC", "O"]:
            # Update the custom role fields if they exist in the profile
            if hasattr(profile, "custom_coach_role"):
                profile.coach_role = team_contributor.role
                profile.custom_coach_role = team_contributor.custom_role
                profile.save()
            elif hasattr(profile, "custom_club_role"):
                profile.club_role = team_contributor.role
                profile.custom_club_role = team_contributor.custom_role
                profile.save()
        else:
            # Normal role update logic
            if hasattr(profile, "coach_role"):
                profile.coach_role = team_contributor.role
                profile.save()
            elif hasattr(profile, "club_role"):
                profile.club_role = team_contributor.role
                profile.save()


class LanguageService:
    @staticmethod
    def get_language_by_id(language_id: int) -> models.Language:
        """Get a language by id."""
        try:
            language = models.Language.objects.get(id=language_id)
            return language
        except models.Language.DoesNotExist:
            raise errors.LanguageDoesNotExistException()
        except TypeError:
            raise errors.ExpectedIntException

    @staticmethod
    def get_language_by_code(code: str) -> models.Language:
        """Get a Language by code."""
        try:
            language = models.Language.objects.get(code=code)
            return language
        except models.Language.DoesNotExist:
            raise errors.LanguageDoesNotExistException()
        except TypeError:
            raise errors.ExpectedIntException


class TransferStatusService:
    """Service for transfer status operation."""

    @staticmethod
    def prepare_generic_type_content(
        content: dict, profile: models.BaseProfile
    ) -> dict:
        """Prepare generic type content for transfer status"""
        content["content_type"] = ContentType.objects.get_for_model(profile)
        content["object_id"] = profile.pk
        return content

    def get_transfer_status_by_id(
        self, transfer_status_id: int
    ) -> typing.Optional[typing.Dict[str, str]]:
        """Get a transfer status by id."""
        result: list = self.get_list_transfer_statutes(id=transfer_status_id)
        return result[0] if result else None

    @staticmethod
    def get_list_transfer_statutes(**search_kwargs) -> typing.List[dict]:
        """Get a list of transfer statuses. If param is provided, filter results."""
        lambda_function: typing.Callable = lambda transfer: True
        if transfer_id := search_kwargs.get("id"):
            lambda_function = lambda transfer: transfer[0] == str(  # noqa: E731
                transfer_id
            )

        result = [
            ChoicesTuple(*transfer)._asdict()
            for transfer in TRANSFER_STATUS_CHOICES_WITH_UNDEFINED
            if lambda_function(transfer)
        ]
        return result


class TransferRequestService:
    """Service for transfer request operation."""

    def get_transfer_request_status_by_id(
        self, transfer_status_id: typing.Union[int, str]
    ) -> typing.Optional[typing.Dict[str, str]]:
        """Get a transfer status by id."""
        result: list = self.__get_list_transfer_request_choices(
            id=transfer_status_id, choices_tuple=TRANSFER_REQUEST_STATUS_CHOICES
        )
        return result[0] if result else None

    def get_num_of_trainings_by_id(
        self, trainings_id: typing.Union[int, str]
    ) -> typing.Optional[typing.Dict[str, str]]:
        """Get a transfer status by number of trainings id."""
        result: list = self.__get_list_transfer_request_choices(
            id=trainings_id, choices_tuple=TRANSFER_TRAININGS_CHOICES
        )
        return result[0] if result else None

    def get_additional_info_by_id(
        self, info_id: int
    ) -> typing.Optional[typing.Dict[str, str]]:
        """Get a transfer status by additional information id."""
        result: list = self.__get_list_transfer_request_choices(
            id=info_id, choices_tuple=TRANSFER_BENEFITS_CHOICES
        )
        return result[0] if result else None

    def get_salary_by_id(
        self, salary_id: typing.Union[int, str]
    ) -> typing.Optional[typing.Dict[str, str]]:
        """Get a transfer status by salary id."""
        result: list = self.__get_list_transfer_request_choices(
            id=salary_id, choices_tuple=TRANSFER_SALARY_CHOICES
        )
        return result[0] if result else None

    def get_list_transfer_statutes(self) -> typing.List[dict]:
        """Get a list of transfer statuses for specified status choices."""
        return self.__get_list_transfer_request_choices(
            choices_tuple=TRANSFER_REQUEST_STATUS_CHOICES
        )

    def get_list_transfer_num_of_trainings(self) -> typing.List[dict]:
        """Get a list of transfer statuses for specified number of trainings choices."""
        return self.__get_list_transfer_request_choices(
            choices_tuple=TRANSFER_TRAININGS_CHOICES
        )

    def get_list_transfer_additional_info(self) -> typing.List[dict]:
        """
        Get a list of transfer statuses for specified additional information choices.
        """
        return self.__get_list_transfer_request_choices(
            choices_tuple=TRANSFER_BENEFITS_CHOICES
        )

    def get_list_transfer_salary(self) -> typing.List[dict]:
        """Get a list of transfer statuses for specified salary choices."""
        return self.__get_list_transfer_request_choices(
            choices_tuple=TRANSFER_SALARY_CHOICES
        )

    @staticmethod
    def __get_list_transfer_request_choices(
        choices_tuple: typing.Tuple, **search_kwargs
    ) -> typing.List[dict]:
        """Get a list of transfer statuses. If param is provided, filter results."""
        lambda_function: typing.Callable = lambda transfer: True
        if transfer_id := search_kwargs.get("id"):
            lambda_function = lambda transfer: transfer[0] == str(  # noqa: E731
                transfer_id
            )

        result = [
            ChoicesTuple(*transfer)._asdict()
            for transfer in choices_tuple
            if lambda_function(transfer)
        ]
        return result


class ProfileVisitHistoryService:
    model = models.ProfileVisitHistory

    def filter(self, **kwargs) -> QuerySet:
        """Filter profile visit history based on given parameters."""
        return self.model.objects.filter(**kwargs)

    def get_user_profile_visit_history(self, **kwargs) -> models.ProfileVisitHistory:
        """
        Retrieve a specific profile visit history based on given parameters.

        Raises errors.ProfileVisitHistoryDoesNotExistException if no history is found.
        """

        try:
            return self.model.objects.get(**kwargs)
        except ObjectDoesNotExist:
            raise errors.ProfileVisitHistoryDoesNotExistException()

    @staticmethod
    def increment(
        instance: ProfileVisitHistoryProtocol,
        requestor: typing.Union[BaseProfile, AnonymousUser],
    ) -> None:
        """Increment the profile visit count for a user."""
        instance.increment(requestor=requestor)

    def create(self, **kwargs) -> models.ProfileVisitHistory:
        """Create a new profile visit history entry with specified kwargs."""
        return self.model.objects.create(**kwargs)

    def profile_visit_history_last_month(self, user: User) -> int:
        """Get the total number of visits for a user in the last 30 days."""
        return self.model.total_visits_from_range(
            user=user, date=utils.get_past_date(days=30)
        )


class RandomizationService:
    @staticmethod
    def get_daily_user_seed(user: User) -> int:
        """
        Generates a daily unique seed for randomization based on the user's identity.

        This method ensures that the seed changes daily and is unique to each user,
        providing a consistent randomized order of querysets for each user
        across requests.
        """
        current_date = datetime.datetime.now().date().isoformat()
        default_identifier = "default-guest-id"
        identifier = str(user.id) if user.is_authenticated else default_identifier
        seed_input = f"{identifier}:{current_date}"
        seed = int(hashlib.sha256(seed_input.encode()).hexdigest(), 16) % (10**8)
        return seed

    def apply_seeded_randomization(self, queryset: QuerySet, user: User) -> QuerySet:
        """
        Applies a seeded randomization to a queryset based on a daily unique seed.

        The randomization ensures that the order of items in the queryset is consistently
        randomized across requests for a given user and changes daily. This method is
        particularly useful for providing each user with a unique perspective of dataset
        listings that refresh daily.
        """
        seed = RandomizationService.get_daily_user_seed(user)
        with connection.cursor() as cursor:
            cursor.execute("SELECT setseed(%s)", [seed / float(10**8)])
        queryset = queryset.order_by("data_fulfill_status", "?")
        return queryset
