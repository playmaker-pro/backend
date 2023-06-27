import logging
from typing import Optional, Type
from django.contrib.auth import get_user_model
from clubs.models import Club as CClub
from clubs.models import Team as CTeam
from . import models
from clubs import models as clubs_models
from .models import PROFILE_TYPE, MODEL_MAP

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
    def set_initial_verification(self, profile: Type[PROFILE_TYPE]) -> None:
        """set initial verification status object if not present"""
        if profile.verification is None:
            profile.verification = models.ProfileVerificationStatus.create_initial(
                profile.user
            )
            profile.save()

    def set_and_create_user_profile(self, user: User) -> Type[PROFILE_TYPE]:
        """get type of profile and create profile"""
        profile_model = MODEL_MAP.get(user.role, models.GuestProfile)
        profile, _ = profile_model.objects.get_or_create(user=user)
        if user.is_player:
            models.PlayerMetrics.objects.get_or_create(player=profile)

        return profile

    def create_profile_with_initial_data(
        self, profile_type: Type[PROFILE_TYPE], data: dict
    ) -> None:
        """Create profile based on type, save with initial data"""
        profile_type.objects.create(**data)

    def get_model_by_role(self, role: str) -> Type[PROFILE_TYPE]:
        """Get and return type of profile based on role (i.e.: 'S', 'P', 'C')"""
        return MODEL_MAP[role]
