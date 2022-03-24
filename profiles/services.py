from re import T
from roles import definitions
from . import models
from django.contrib.auth import get_user_model
import logging
from clubs.models import Team as CTeam
from clubs.models import Club as CClub

logger = logging.getLogger(__name__)


User = get_user_model()


class ProfileVerificationService:
    """Profile verification service which can mange verification process for user's profile"""

    def __init__(self, profile: models.BaseProfile) -> None:
        self.profile = profile
        self.user = self.profile.user

    def verify(self):
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

    def update_verification_data(self, data: dict, requestor: User = None) -> models.ProfileVerificationStatus:
        """using dict-like data we can create new verification object"""
        logger.debug(f"New verification recieved for {self.user}")
        team = None
        club = None
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
                team = data.get("team")
        else:
            if self.user.is_club:
                club = data.get("team")
            else:
                team = None

                
        set_by = requestor or User.get_system_user()
        new = models.ProfileVerificationStatus.create(
            owner=self.user,
            previous=self.profile.verification,
            has_team=has_team,
            team_not_found=team_not_found,
            club=club,
            team=team,
            set_by=set_by
        )
        self.profile.verification = new
        self.profile.save()
        return new

    def update_verification_status(self, status: str, verification: models.ProfileVerificationStatus = None ) -> None:
        verification = self.profile.verification or verification
        verification.status = status
        verification.save()
        
    def _verify_user(self):
        self.user.verify()
        self.user.save()

    def _verify_player(self):
        profile = self.profile

        if profile.verification.has_team and profile.verification.team:
            profile.team_object = profile.verification.team
            self._verify_user()

        elif (
            profile.verification.has_team is True
            and profile.verification.team_not_found is True
            and profile.team_club_league_voivodeship_ver
        ):
            profile.team_object = None
            self._verify_user()

        elif (
            profile.verification.has_team is False
            and not profile.team_club_league_voivodeship_ver
        ):
            profile.team_object = None
            self._verify_user()
        elif (
            profile.verification.has_team is False
            and profile.team_club_league_voivodeship_ver
        ):
            profile.team_object = None
        profile.save()

    def _verify_coach(self) -> None:
        profile = self.profile

        if profile.verification.has_team and profile.verification.team:
            profile.team_object = profile.verification.team
            profile.save()

            if hasattr(profile.user, 'managed_team'):
                managed_team_id = profile.user.managed_team.id
                team = CTeam.objects.get(id=managed_team_id)
                team.visible = False
                team.manager = None
                team.save()

            if not profile.team_object.manager:
                profile.team_object.manager = profile.user
                profile.team_object.visible = True
                profile.team_object.save()

            if hasattr(profile.user, 'managed_club'):
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
            and profile.team_club_league_voivodeship_ver
        ):
            self._verify_user()

        elif (
            profile.verification.has_team is False
            and not profile.team_club_league_voivodeship_ver
        ):
            self._verify_user()
        elif (
            profile.verification.has_team is False
            and profile.team_club_league_voivodeship_ver
        ):
            profile.team_object = None

            self._verify_user()
        profile.save()

    def _verify_club(self) -> None:
        profile = self.profile
        if profile.verification.has_team and profile.verification.club:
            profile.club_object = profile.verification.club
            profile.save()

            for t in profile.verification.club.teams.all():
                t.visible = True
                t.save()

            if hasattr(profile.user, 'managed_club'):
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
            and profile.team_club_league_voivodeship_ver
        ):
            profile.club_object = None
            if hasattr(profile.user, 'managed_club'):
                managed_club_id = profile.user.managed_club.id
                clubb = CClub.objects.get(id=managed_club_id)
                clubb.manager = None
                clubb.save()

            profile.save()
            self._verify_user()

        elif (
            profile.verification.has_team is False
            and not profile.team_club_league_voivodeship_ver
        ):
            self._verify_user()
        elif (
            profile.verification.has_team is False
            and profile.team_club_league_voivodeship_ver
        ):
            profile.club_object = None
            if hasattr(profile.user, 'managed_club'):
                managed_club_id = profile.user.managed_club.id
                clubb = CClub.objects.get(id=managed_club_id)
                clubb.manager = None
                clubb.save()

            profile.save()
            self._verify_user()


class ProfileService:
    def set_initial_verification(self, profile):
        # set initial verification status object if not present
        if profile.verification is None:
            profile.verification = models.ProfileVerificationStatus.create_initial(
                profile.user
            )
            profile.save()

    def set_and_create_user_profile(self, user):
        model_map = {
            definitions.PLAYER_SHORT: models.PlayerProfile,
            definitions.COACH_SHORT: models.CoachProfile,
            definitions.CLUB_SHORT: models.ClubProfile,
            definitions.SCOUT_SHORT: models.ScoutProfile,
            definitions.MANAGER_SHORT: models.ManagerProfile,
            definitions.PARENT_SHORT: models.ParentProfile,
            definitions.GUEST_SHORT: models.GuestProfile,
        }
        profile_model = model_map.get(user.role, models.GuestProfile)

        profile, _ = profile_model.objects.get_or_create(user=user)

        # custom things for player accout
        # we need to attach metrics to PLayer's profile
        if user.is_player:
            models.PlayerMetrics.objects.get_or_create(player=profile)
        return profile
