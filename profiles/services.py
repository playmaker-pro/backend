import datetime
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
from profiles import api_errors, errors, models, utils
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
                return profile.user
            except model.DoesNotExist:
                continue
        else:
            raise ObjectDoesNotExist

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

        potential_matches = User.objects.all()

        matching_users = filter(
            lambda user: search_term
            in utils.preprocess_search_term(
                (user.first_name or "") + (user.last_name or "")
            ),
            potential_matches,
        )

        matching_users_ids = [user.id for user in matching_users]
        return User.objects.filter(id__in=matching_users_ids)

    @staticmethod
    def is_player_profile(profile) -> bool:
        return type(profile).__name__.lower() == "playerprofile"

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

    @staticmethod
    def get_teams_for_profile(profile_uuid: uuid.UUID) -> django_base_models.QuerySet:
        """
        Fetches all the teams associated with a given profile, following the model's Meta ordering.
        """
        return (
            models.TeamContributor.objects.filter(profile_uuid=profile_uuid)
            .distinct("id")
            .order_by("id")
        )

    @staticmethod
    def create_or_get_team_contributor(
        profile_uuid: uuid.UUID, team_history: clubs_models.TeamHistory, **kwargs
    ) -> typing.Tuple[models.TeamContributor, bool]:
        """
        Create or retrieve a TeamContributor instance for a given profile
        and team history.
        """
        criteria = {
            "profile_uuid": profile_uuid,
            **kwargs,
        }

        existing_contributor = models.TeamContributor.objects.filter(
            **criteria, team_history=team_history
        ).first()

        if existing_contributor:
            return existing_contributor, False

        team_contributor_instance = models.TeamContributor.objects.create(**criteria)
        team_contributor_instance.team_history.add(team_history)

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
        is_primary: bool,
        season: typing.Optional[str] = None,
        round_val: typing.Optional[str] = None,
        profile_type: str = "playerprofile",
    ) -> None:
        """
        Handle setting is_primary attribute and checking for existing primary
        contributors.
        """

        if is_primary:
            if profile_type == "playerprofile":
                # Unset any existing primary contributors with the same profile, season, round
                models.TeamContributor.objects.filter(
                    profile_uuid=profile_uuid,
                    team_history__league_history__season=season,
                    is_primary=True,
                    round=round_val,
                ).exclude(id=team_contributor.id).update(is_primary=False)

            else:
                # Unset any existing primary contributors for non-players
                contributors_to_unset = models.TeamContributor.objects.filter(
                    profile_uuid=profile_uuid, is_primary=True
                ).exclude(id=team_contributor.id)

                # Set their end date to today
                contributors_to_unset.update(
                    is_primary=False, end_date=datetime.date.today()
                )

            # Set the given team_contributor as primary
            team_contributor.is_primary = True
            team_contributor.end_date = None
        else:
            team_contributor.is_primary = False

        team_contributor.save()

    @staticmethod
    def delete_team_contributor(team_contributor: models.TeamContributor) -> None:
        """
        Delete a TeamContributor instance.
        """
        team_contributor.delete()

    def unified_fetch_related_entities(
        self, data: dict, profile_uuid: uuid.UUID, profile_type: str
    ) -> typing.Tuple:
        """
        Fetch or create team, league, league history, and team history based on the profile type.
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
        Create a contributor, either a player or a non-player, based on the provided data and profile UUID.
        """
        # Common logic
        criteria = {}
        matched_team_histories = self.get_or_create_team_history(data, profile_uuid)

        # Player-specific logic
        if is_player:
            criteria["round"] = data.get("round")
            existing_contributor: models.TeamContributor = (
                self.check_existing_contributor(
                    {
                        "profile_uuid": profile_uuid,
                        "team_history__in": matched_team_histories,
                        "round": data.get("round"),
                    }
                )
            )

        # Non-player specific logic
        else:
            criteria["role"] = data.get("role")
            criteria["start_date"] = data["start_date"]
            criteria["end_date"] = data.get("end_date", None)
            existing_contributor = self.check_existing_contributor(
                {
                    "profile_uuid": profile_uuid,
                    "role": data.get("role"),
                    "start_date": data.get("start_date"),
                }
            )
        # Check if existing contributor
        if existing_contributor:
            raise errors.TeamContributorAlreadyExistServiceException()

        # Create or get the team contributor
        team_contributor, was_created = self.create_or_get_team_contributor(
            profile_uuid, matched_team_histories[0], **criteria
        )

        if not was_created:
            raise errors.TeamContributorAlreadyExistServiceException()

        # Handle primary contributor logic
        team_contributor.team_history.set(matched_team_histories)
        self.handle_primary_contributor(
            team_contributor=team_contributor,
            profile_uuid=profile_uuid,
            is_primary=data.get("is_primary", False),
            profile_type="player" if is_player else "non-player",
        )

        return team_contributor

    def get_or_create_team_history(
        self, data: dict, profile_uuid: uuid.UUID
    ) -> typing.List[typing.Union[clubs_models.TeamHistory, typing.Any]]:
        """
        Retrieve or create a team history based on the provided data and profile UUID.
        """
        is_player = "round" in data  # Using "season" as the distinguishing factor

        # If a team_history is provided, fetch it
        if "team_history" in data and data["team_history"]:
            team_history_instance, _ = self.fetch_related_data(data, profile_uuid)

            if not is_player:  # non-player scenario
                # Extract attributes from team_history_instance, for example:
                team_parameter = team_history_instance.team.id
                league_identifier = team_history_instance.league_history.league.id

                # Use these extracted values to call create_or_get_team_history_date_based
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
        team_histories: typing.List[clubs_models.TeamHistory],
    ):
        """
        Update attributes of a TeamContributor instance based on provided data.

        This function updates various attributes of a given team contributor instance.
        It sets the team history, primary status, round (if applicable), and then saves the changes.
        """
        team_contributor.team_history.set(team_histories)
        team_contributor.is_primary = data.get("is_primary", False)
        if "round" in data:
            team_contributor.round = data.get("round")
        team_contributor.save()

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
        provided criteria and raises an exception if one exists. If the contributor is marked
        as primary, the function handles the primary contributor logic. Finally, the function
        updates the team contributor instance with the new data provided.
        """
        team_history_instance = team_contributor.team_history.first()

        # First, get the current attributes of the team_contributor for a player
        if team_history_instance:
            current_data = {
                "round": team_contributor.round,
                "team_parameter": team_history_instance.team.id,
                "league_identifier": team_history_instance.league_history.league.id,
                "season": team_history_instance.season,
            }

        # Overwrite the current_data dictionary with the provided data.
        current_data.update(data)
        profile_type = "player"
        team_history, season = self.fetch_related_data(data, profile_uuid, profile_type)

        existing_contributor: models.TeamContributor = self.check_existing_contributor(
            {
                "profile_uuid": profile_uuid,
                "team_history__in": [team_history],
                "round": data.get("round"),
            },
            team_contributor.pk,
        )

        if existing_contributor:
            raise errors.TeamContributorAlreadyExistServiceException()

        self.handle_primary_contributor(
            team_contributor,
            profile_uuid,
            data.get("is_primary", False),
            season,
            data.get("round"),
        )

        self.update_team_contributor(team_contributor, data, [team_history])
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
        relevant team history based on the input data. It then updates the team contributor
        instance with the new data provided.
        """
        team_history_instance = team_contributor.team_history.first()

        # First, get the current attributes of the team_contributor
        if team_history_instance:
            current_data = {
                "start_date": team_contributor.start_date,
                "end_date": team_contributor.end_date,
                "team_parameter": team_history_instance.team.id,
                "league_identifier": team_history_instance.league_history.league.id,
                "is_primary": team_contributor.is_primary,
                "role": team_contributor.role,
            }

        # Now, overwrite the current_data dictionary with the provided data.
        current_data.update(data)

        if "team_history" in current_data and current_data["team_history"]:
            team_history_instance, season = self.fetch_related_data(
                current_data, profile_uuid, None
            )
            matched_team_histories = [team_history_instance]
        else:
            matched_team_histories = (
                club_services.create_or_get_team_history_date_based(
                    current_data["start_date"],
                    current_data["end_date"],
                    current_data["team_parameter"],
                    current_data["league_identifier"],
                    current_data.get("country", "PL"),
                    self.profile_service.get_user_by_uuid(profile_uuid),
                )
            )

        existing_contributor: models.TeamContributor = self.check_existing_contributor(
            {
                "profile_uuid": profile_uuid,
                "role": current_data.get("role"),
                "start_date": current_data.get("start_date"),
                "end_date": current_data.get("end_date"),
                "team_history__in": matched_team_histories,
            },
            team_contributor.pk,
        )

        if existing_contributor:
            raise errors.TeamContributorAlreadyExistServiceException()

        team_contributor.role = current_data.get("role")
        team_contributor.start_date = current_data.get("start_date")
        team_contributor.end_date = current_data.get("end_date")

        self.handle_primary_contributor(
            team_contributor,
            profile_uuid,
            current_data.get("is_primary", False),
            profile_type="nonplayerprofile",
        )
        self.update_team_contributor(
            team_contributor, current_data, matched_team_histories
        )

        return team_contributor


class LanguageService:
    @staticmethod
    def get_language_by_id(language_id: int) -> models.Language:
        """Get a language by id."""

        try:
            language = models.Language.objects.get(id=language_id)
            return language
        except models.Language.DoesNotExist:
            raise errors.LanguageDoesNotExistException()
