import logging
import typing
import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models as django_base_models
from django.db.models import ObjectDoesNotExist
from django.db.models import functions as django_base_functions
from pydantic import BaseModel

from api.services import LocaleDataService
from clubs import models as clubs_models
from clubs import services as club_services
from clubs.models import Club as CClub
from clubs.models import Team as CTeam
from profiles import errors, models, utils
from profiles.models import REVERSED_MODEL_MAP
from roles.definitions import CLUB_ROLES, PROFILE_TYPE_MAP
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
    """Profile verification service which can manage verification process for user's profile"""

    def __init__(self, profile: models.BaseProfile) -> None:
        self.profile: models.BaseProfile = profile
        self.user: User = self.profile.user

    def verify(self) -> None:
        if not self.user.validate_last_name():
            self.user.unverify()
            self.user.save()
            logger.info(
                f"User {self.user} has invalid last_name ={self.user.last_name}. Minimum 2char needed."
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

    @staticmethod
    def get_user_by_uuid(profile_uuid: uuid.UUID) -> User:
        """Fetches a profile by its UUID."""

        for model in models.PROFILE_MODELS:
            try:
                profile = model.objects.get(uuid=profile_uuid)
                return profile.user.id
            except model.DoesNotExist:
                continue
        else:
            raise ObjectDoesNotExist

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

        # Translate the short definition to the related type string using PROFILE_TYPE_MAP
        related_type = PROFILE_TYPE_MAP.get(short_definition)

        return related_type


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
    def filter_player_league(
        queryset: django_base_models.QuerySet, league_ids: list
    ) -> django_base_models.QuerySet:
        """Filter player's queryset with list of highest_parent league_id's using current season name"""
        current_season = get_current_season()
        return queryset.filter(
            team_object__historical__league_history__season__name=current_season,
            team_object__historical__league_history__league__highest_parent__in=league_ids,
        )

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
        """Validate each country code, then return queryset filtered by given countries"""
        return queryset.filter(
            user__userpreferences__citizenship__overlap=[
                locale_service.validate_country_code(code) for code in country
            ]
        )

    @staticmethod
    def filter_language(
        queryset: django_base_models.QuerySet, language: list
    ) -> django_base_models.QuerySet:
        """Validate each language code, then return queryset filtered by given spoken languages"""
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


class PlayerProfilePositionService:
    def validate_positions(self, positions_data: typing.List[PositionData]) -> None:
        """
        Validates the given positions data.

        raises MultipleMainPositionError: If more than one main position is found.
        raises TooManyAlternatePositionsError: If more than two non-main positions are found.
        """
        main_positions_count = len([data for data in positions_data if data.is_main])
        non_main_positions_count = len(
            [data for data in positions_data if not data.is_main]
        )

        if main_positions_count > 1:
            raise errors.MultipleMainPositionError

        if non_main_positions_count > 2:
            raise errors.TooManyAlternatePositionsError

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
        changed, it is created or updated accordingly. Non-main positions are also created
        or updated, but no more than two are allowed.

        If any positions from the original set are not in the new positions data, they
        are deleted.
        """
        # Validate that the provided positions data meets the necessary criteria.
        self.validate_positions(positions_data)

        # Get the current positions associated with the profile, indexed by their player_position_id.
        current_positions = {
            position.player_position_id: position
            for position in profile.player_positions.all()
        }

        # Initialize lists to hold positions that need to be created and updated.
        positions_to_create = []
        positions_to_update = []
        # Initialize a set to hold the IDs of positions that should be retained (i.e., not deleted).
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
            position.save()


class ProfileVideoService:
    @staticmethod
    def get_player_video_labels() -> tuple:
        """Get player video labels"""
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

    @staticmethod
    def set_as_primary(
        profile_uuid: uuid.UUID, team_contributor: models.TeamContributor
    ) -> None:
        """
        Sets a given TeamContributor as the primary for a profile.
        This will unset any existing primary TeamContributor for the profile.
        """
        # Unset any existing primary team contributors for the profile
        models.TeamContributor.objects.filter(
            profile_uuid=profile_uuid, is_primary=True
        ).update(is_primary=False)

        # Set the given team_contributor as primary
        team_contributor.is_primary = True
        team_contributor.save()

    @staticmethod
    def get_teams_for_profile(profile_uuid: uuid.UUID) -> django_base_models.QuerySet:
        """
        Fetches all the teams associated with a given profile.
        """
        return models.TeamContributor.objects.filter(profile_uuid=profile_uuid)

    @staticmethod
    def create_or_get_team_contributor(
        profile_uuid: uuid.UUID,
        team_history: clubs_models.TeamHistory,
        round_val: typing.Optional[str] = None,
    ) -> typing.Tuple[models.TeamContributor, bool]:
        """
        Create or retrieve a TeamContributor instance for a given profile
        and team history.
        """
        try:
            team_contributor_instance = models.TeamContributor.objects.get(
                profile_uuid=profile_uuid, round=round_val, team_history=team_history
            )
            created = False
        except models.TeamContributor.DoesNotExist:
            team_contributor_instance = models.TeamContributor.objects.create(
                profile_uuid=profile_uuid, round=round_val
            )
            team_contributor_instance.team_history.add(team_history)
            created = True

        return team_contributor_instance, created

    @staticmethod
    def handle_primary_contributor(
        team_contributor: models.TeamContributor,
        season: str,
        profile_uuid: uuid.UUID,
        is_primary: bool,
        round_val: typing.Optional[str] = None,
    ) -> None:
        """
        Handle setting is_primary attribute and checking for existing primary
        contributors.
        """

        if is_primary:
            # Unset any existing primary contributors with the same profile, season, round
            models.TeamContributor.objects.filter(
                profile_uuid=profile_uuid,
                team_history__league_history__season=season,
                is_primary=True,
                round=round_val,
            ).exclude(id=team_contributor.id).update(is_primary=False)

            # Set the given team_contributor as primary
            team_contributor.is_primary = True
        else:
            team_contributor.is_primary = False

        team_contributor.save()

    def fetch_related_entities(
        self,
        data: typing.Dict[str, typing.Union[str, bool, int]],
        profile_uuid: uuid.UUID,
    ) -> typing.Tuple:
        """
        Fetch team, league, league_history, and team_history.
        """
        league_identifier: typing.Union[str, int] = data.get("league_identifier")
        country_code: str = data.get("country", "PL")
        season: int = data.get("season")
        user = self.profile_service.get_user_by_uuid(profile_uuid)
        team: clubs_models.Team = club_services.get_or_create(data, user, country_code)
        league, league_history = club_services.create_or_get_league_and_history(
            league_identifier, country_code, season, user, data
        )

        team_history: clubs_models.TeamHistory = (
            club_services.create_or_get_team_history(team, league_history, user)
        )

        return team, league, league_history, team_history, season

    def ensure_unique_team_contributor_and_related(
        self,
        profile_uuid: uuid.UUID,
        data: typing.Dict[str, typing.Union[str, bool]],
    ) -> models.TeamContributor:
        """
        Creates or gets all related entities for a given profile and provided data.
        """
        round_value: str = data.get("round")
        is_primary: bool = data.get("is_primary")

        if "team_history" in data and data["team_history"]:
            team_history_instance = (
                data["team_history"][0]
                if isinstance(data["team_history"], list)
                else data["team_history"]
            )
            team_history, season = club_services.fetch_team_history_and_season(
                team_history_instance.id
            )
        else:
            (
                team,
                league,
                league_history,
                team_history,
                season,
            ) = self.fetch_related_entities(data, profile_uuid)

        # Check for existing contributor before making any modifications
        existing_contributor = models.TeamContributor.objects.filter(
            profile_uuid=profile_uuid,
            team_history__in=[team_history],
            round=data.get("round"),
        ).first()
        if existing_contributor:
            raise errors.TeamContributorAlreadyExistServiceException()

        team_contributor, was_created = self.create_or_get_team_contributor(
            profile_uuid, team_history, round_value
        )

        self.handle_primary_contributor(
            team_contributor,
            season,
            profile_uuid,
            is_primary,
            round_value,
        )

        if not was_created:
            raise errors.TeamContributorAlreadyExistServiceException()

        return team_contributor

    def update_related_entities(
        self,
        profile_uuid: uuid.UUID,
        team_contributor: models.TeamContributor,
        data: typing.Dict[str, typing.Union[str, bool, int]],
    ) -> models.TeamContributor:
        """
        Update related entities for a given profile, team_contributor,
        and provided data.
        """
        round_value: str = data.get("round")
        is_primary: bool = data.get("is_primary")
        if "team_history" in data and data["team_history"]:
            team_history_instance = (
                data["team_history"][0]
                if isinstance(data["team_history"], list)
                else data["team_history"]
            )
            team_history, season = club_services.fetch_team_history_and_season(
                team_history_instance.id
            )
        else:
            (
                team,
                league,
                league_history,
                team_history,
                season,
            ) = self.fetch_related_entities(data, profile_uuid)

        existing_contributor = (
            models.TeamContributor.objects.filter(
                profile_uuid=profile_uuid,
                team_history__in=[team_history],  # Use __in for M2M lookup
                round=round_value,
            )
            .exclude(id=team_contributor.pk)
            .first()
        )

        if existing_contributor:
            raise errors.TeamContributorAlreadyExistServiceException()

        self.handle_primary_contributor(
            team_contributor, season, profile_uuid, is_primary, round_value
        )

        # Clear previous team_histories and set the new one
        team_contributor.team_history.clear()
        team_contributor.team_history.add(team_history)

        team_contributor.round = round_value
        team_contributor.save()

        return team_contributor

    @staticmethod
    def delete_team_contributor(team_contributor: models.TeamContributor) -> None:
        """
        Delete a TeamContributor instance.
        """
        team_contributor.delete()


class LanguageService:
    @staticmethod
    def get_language_by_id(language_id: int) -> models.Language:
        """Get a language by id."""

        try:
            language = models.Language.objects.get(id=language_id)
            return language
        except models.Language.DoesNotExist:
            raise errors.LanguageDoesNotExistException()
