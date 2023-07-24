import logging
from typing import Optional, Type, Union, List
import uuid
from django.contrib.auth import get_user_model
from clubs.models import Club as CClub
from clubs.models import Team as CTeam
from . import models
from clubs import models as clubs_models
from .errors import ProfileDoesNotExist, AlternatePositionValidationError, MainPositionValidationError
from .models import PlayerProfilePosition

logger = logging.getLogger(__name__)
User = get_user_model()


class ProfileVerificationService:
    """Profile verification service which can mange verification process for user's profile"""

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
        team: Optional[clubs_models.Team] = None
        team_history: Optional[clubs_models.TeamHistory] = None
        club: Optional[clubs_models.Club] = None
        text: Optional[str] = None

        if team_club_league_voivodeship_ver := data.get(
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
        return models.PROFILE_MODEL_MAP[role]

    def get_role_by_model(self, model: Type[models.PROFILE_TYPE]) -> str:
        """Get and return role shortcut based on profile type"""
        return models.REVERSED_MODEL_MAP[model]

    def get_profile_by_uuid(
        self, profile_uuid: Union[uuid.UUID, str]
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
        raise ProfileDoesNotExist

    def is_valid_uuid(self, value: str) -> bool:
        try:
            uuid_obj = uuid.UUID(value)
        except ValueError:
            return False
        return str(uuid_obj) == value


# profiles/services.py

class PlayerPositionService:
    def update_positions(self, profile, positions_data):
        # Get the existing positions
        current_positions = {position.player_position_id: position for position in profile.player_positions.all()}

        # Separate main and non-main positions
        main_position = None
        non_main_positions = []
        for pos in current_positions.values():
            if pos.is_main:
                main_position = pos
            else:
                non_main_positions.append(pos)

        # Variables to keep track of created/updated non-main positions
        non_main_positions_created_or_updated = 0
        non_main_positions_to_update = min(2, len(non_main_positions))

        # Count the main and non-main positions in positions_data
        main_positions_count = len([data for data in positions_data if data["is_main"]])
        non_main_positions_count = len([data for data in positions_data if not data["is_main"]])

        # Raise an error if there's more than one main position
        if main_positions_count > 1:
            raise MainPositionValidationError

        # Raise an error if there are more than two non-main positions
        if non_main_positions_count > 2:
            raise AlternatePositionValidationError

        # Iterate over new positions
        for position_data in positions_data:
            player_position_id = position_data["player_position"]
            is_main = position_data["is_main"]

            # Handle main position
            if is_main:
                if main_position is None:  # If no main position exists, create it
                    PlayerProfilePosition.objects.create(player_profile=profile, player_position_id=player_position_id,
                                                         is_main=True)
                elif main_position.player_position_id != player_position_id:  # If main position has changed, update it
                    main_position.player_position_id = player_position_id
                    main_position.save()

            # Handle non-main positions
            else:
                if non_main_positions_created_or_updated < non_main_positions_to_update:  # If we can still update existing non-main positions, do so
                    non_main_positions[non_main_positions_created_or_updated].player_position_id = player_position_id
                    non_main_positions[non_main_positions_created_or_updated].save()
                    non_main_positions_created_or_updated += 1
                elif non_main_positions_created_or_updated < 2:  # If we can still create new non-main positions, do so
                    PlayerProfilePosition.objects.create(player_profile=profile, player_position_id=player_position_id,
                                                         is_main=False)
                    non_main_positions_created_or_updated += 1
                else:  # If we already have two non-main positions, raise an error
                    raise AlternatePositionValidationError

        # Delete unused positions
        self.delete_unused_positions(profile, positions_data)

    def create_position(self, profile, player_position_id, is_main):
        """
        Create a new player position for the given profile.
        :param profile: The profile instance to create the position for.
        :param player_position_id: The ID of the player position to create.
        :param is_main: Boolean indicating if this is the main position for the player.
        """
        if is_main:
            main_positions = profile.player_positions.filter(is_main=True)
            if main_positions.exists():
                raise MainPositionValidationError
        else:
            non_main_positions = profile.player_positions.filter(is_main=False)
            if non_main_positions.count() >= 2:
                raise AlternatePositionValidationError

        position_data = {"player_position_id": player_position_id, "is_main": is_main}
        PlayerProfilePosition.objects.create(player_profile=profile, **position_data)

    def delete_unused_positions(self, profile, positions):
        """
        Delete any player positions that were not included in the API data.
        :param profile: The profile instance to delete unused positions from.
        :param positions: List of dictionaries containing position data from the API.
                          Example format: [{"player_position": 1, "is_main": True}, ...]
        """
        existing_positions = profile.player_positions.all()
        existing_position_ids = set(pos.player_position_id for pos in existing_positions)
        updated_position_ids = set(pos_data["player_position"] for pos_data in positions)

        positions_to_delete = existing_position_ids - updated_position_ids

        for position_id in positions_to_delete:
            position = existing_positions.get(player_position_id=position_id)
            position.delete()
