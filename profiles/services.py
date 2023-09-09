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
from clubs.models import Club as CClub
from clubs.models import Team as CTeam
from profiles import errors, models, utils
from roles.definitions import CLUB_ROLES
from utils import get_current_season

logger = logging.getLogger(__name__)
User = get_user_model()
locale_service = LocaleDataService()


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
    def set_initial_verification(self, profile: models.PROFILE_TYPE) -> None:
        """set initial verification status object if not present"""
        if profile.verification is None:
            profile.verification = models.ProfileVerificationStatus.create_initial(
                profile.user
            )
            profile.save()

    def set_and_create_user_profile(self, user: User) -> models.PROFILE_TYPE:
        """get type of profile and create profile"""
        profile_model = models.PROFILE_MODEL_MAP.get(user.role, models.GuestProfile)
        profile, _ = profile_model.objects.get_or_create(user=user)
        if user.is_player:
            models.PlayerMetrics.objects.get_or_create(player=profile)

        return profile

    def create_profile_with_initial_data(
        self, profile_type: models.PROFILE_TYPE, data: dict
    ) -> models.PROFILE_TYPE:
        """Create profile based on type, save with initial data"""
        return profile_type.objects.create(**data)

    def get_model_by_role(self, role: str) -> models.PROFILE_TYPE:
        """Get and return type of profile based on role (i.e.: 'S', 'P', 'C')"""
        try:
            return models.PROFILE_MODEL_MAP[role]
        except KeyError:
            raise ValueError("Invalid role shortcut.")

    def get_role_by_model(self, model: typing.Type[models.PROFILE_TYPE]) -> str:
        """Get and return role shortcut based on profile type"""
        return models.REVERSED_MODEL_MAP[model]

    def get_profile_by_uuid(
        self, profile_uuid: typing.Union[uuid.UUID, str]
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

    def is_valid_uuid(self, value: str) -> bool:
        try:
            uuid_obj = uuid.UUID(value)
        except ValueError:
            return False
        return str(uuid_obj) == value

    def get_club_roles(self) -> tuple:
        """Get list of club roles from ClubProfile"""
        return CLUB_ROLES

    @staticmethod
    def get_club_roles_as_dict() -> dict:
        """Get list of club roles from ClubProfile as a dict"""
        return dict(CLUB_ROLES)

    def get_referee_roles(self) -> tuple:
        """Get referee roles from RefereeProfile"""
        return models.RefereeLevel.REFEREE_ROLE_CHOICES

    def filter_youth_players(
        self, queryset: django_base_models.QuerySet
    ) -> django_base_models.QuerySet:
        """Filter profiles queryset to get profiles of youth users (under 21 yo)"""
        max_youth_birth_date = utils.get_past_date(years=21)
        return queryset.filter(
            user__userpreferences__birth_date__gte=max_youth_birth_date
        )

    def filter_min_age(
        self, queryset: django_base_models.QuerySet, age: int
    ) -> django_base_models.QuerySet:
        """Filter profile queryset with minimum user age"""
        min_birth_date = utils.get_past_date(years=age)
        return queryset.filter(user__userpreferences__birth_date__lte=min_birth_date)

    def filter_max_age(
        self, queryset: django_base_models.QuerySet, age: int
    ) -> django_base_models.QuerySet:
        """Filter profile queryset with maximum user age"""
        max_birth_date = utils.get_past_date(years=age + 1)
        return queryset.filter(user__userpreferences__birth_date__gte=max_birth_date)

    def filter_player_position(
        self, queryset: django_base_models.QuerySet, positions: list
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

    def filter_player_league(
        self, queryset: django_base_models.QuerySet, league_ids: list
    ) -> django_base_models.QuerySet:
        """Filter player's queryset with list of highest_parent league_id's using current season name"""
        current_season = get_current_season()
        return queryset.filter(
            team_object__historical__league_history__season__name=current_season,
            team_object__historical__league_history__league__highest_parent__in=league_ids,
        )

    def filter_localization(
        self,
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

    def filter_country(
        self, queryset: django_base_models.QuerySet, country: list
    ) -> django_base_models.QuerySet:
        """Validate each country code, then return queryset filtered by given countries"""
        return queryset.filter(
            user__userpreferences__citizenship__overlap=[
                locale_service.validate_country_code(code) for code in country
            ]
        )

    def filter_language(
        self, queryset: django_base_models.QuerySet, language: list
    ) -> django_base_models.QuerySet:
        """Validate each language code, then return queryset filtered by given spoken languages"""
        return queryset.filter(
            user__userpreferences__spoken_languages__code__in=[
                locale_service.validate_language_code(code) for code in language
            ]
        )

    def get_players_on_age_range(
        self, min_age: int = 14, max_age: int = 44
    ) -> django_base_models.QuerySet:
        """Get queryset of players with age between given args"""
        player_max_age = utils.get_past_date(years=max_age)
        player_min_age = utils.get_past_date(years=min_age)
        return models.PlayerProfile.objects.filter(
            user__userpreferences__birth_date__lte=player_min_age,
            user__userpreferences__birth_date__gte=player_max_age,
        )

    def get_user_profiles(self, user: User) -> typing.List[models.PROFILE_TYPE]:
        """Find all profiles for given user"""
        profiles: list = []
        for profile_type in models.PROFILE_MODELS:
            if profile := profile_type.objects.filter(user=user).first():
                profiles.append(profile)
        return profiles


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


class PlayerVideoService:
    @staticmethod
    def get_player_video_labels() -> tuple:
        """Get player video labels"""
        return models.PlayerVideo.LABELS

    @staticmethod
    def get_video_by_id(_id: int) -> models.PlayerVideo:
        """Get PlayerVideo object by id"""
        return models.PlayerVideo.objects.get(id=_id)  # type: ignore
