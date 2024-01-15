from profiles.api.serializers import (
    AggregatedTeamContributorSerializer,
    OtherProfilesTeamContributorInputSerializer,
    PlayerProfileTeamContributorInputSerializer,
    PlayerTeamContributorSerializer,
)
from profiles.serializers_detailed.club_profile_serializers import (
    ClubProfileUpdateSerializer,
    ClubProfileViewSerializer,
)
from profiles.serializers_detailed.coach_profile_serializers import (
    CoachProfileUpdateSerializer,
    CoachProfileViewSerializer,
)
from profiles.serializers_detailed.guest_profile_serializer import (
    GuestProfileUpdateSerializer,
    GuestProfileViewSerializer,
)
from profiles.serializers_detailed.manager_profile_serializers import (
    ManagerProfileUpdateSerializer,
    ManagerProfileViewSerializer,
)
from profiles.serializers_detailed.player_profile_serializers import (
    PlayerProfileUpdateSerializer,
    PlayerProfileViewSerializer,
)
from profiles.serializers_detailed.scout_profile_serializers import (
    ScoutProfileUpdateSerializer,
    ScoutProfileViewSerializer,
)
from roles.definitions import RoleShortcut


class SerializersManager:
    SERIALIZER_MAPPING = {
        "PlayerProfile": PlayerProfileViewSerializer,
        "PlayerProfile_update": PlayerProfileUpdateSerializer,
        "CoachProfile": CoachProfileViewSerializer,
        "CoachProfile_update": CoachProfileUpdateSerializer,
        "ScoutProfile": ScoutProfileViewSerializer,
        "ScoutProfile_update": ScoutProfileUpdateSerializer,
        "ClubProfile": ClubProfileViewSerializer,
        "ClubProfile_update": ClubProfileUpdateSerializer,
        "GuestProfile": GuestProfileViewSerializer,  # "Fan" profile (kibic)
        "GuestProfile_update": GuestProfileUpdateSerializer,
        "ManagerProfile": ManagerProfileViewSerializer,
        "ManagerProfile_update": ManagerProfileUpdateSerializer,
        # GET /api/v3/profiles?role=
        RoleShortcut.PLAYER: PlayerProfileViewSerializer,
        RoleShortcut.COACH: CoachProfileViewSerializer,
        RoleShortcut.SCOUT: ScoutProfileViewSerializer,
        RoleShortcut.FAN: GuestProfileViewSerializer,
        RoleShortcut.MANAGER: ManagerProfileViewSerializer,
        RoleShortcut.CLUB: ClubProfileViewSerializer,
    }
    PLAYER_PROFILE_TEAM_CONTRIBUTOR_SERIALIZERS = {
        "input": PlayerProfileTeamContributorInputSerializer,
        "output": PlayerTeamContributorSerializer,
    }

    OTHER_PROFILE_TEAM_CONTRIBUTOR_SERIALIZERS = {
        "input": OtherProfilesTeamContributorInputSerializer,
        "output": AggregatedTeamContributorSerializer,
    }

    TEAM_CONTRIBUTOR_SERIALIZER_MAPPING = {
        "PlayerProfile": PLAYER_PROFILE_TEAM_CONTRIBUTOR_SERIALIZERS,
        "GuestProfile": PLAYER_PROFILE_TEAM_CONTRIBUTOR_SERIALIZERS,
        "Default": OTHER_PROFILE_TEAM_CONTRIBUTOR_SERIALIZERS,
    }

    def get_serializer(self, model_name: str):
        return self.SERIALIZER_MAPPING.get(model_name)

    def get_serializer_class(self, profile, direction: str):
        """
        Get the serializer class based on the type of the provided profile and the direction.
        """  # noqa: E501
        return self.get_team_contributor_serializer(type(profile).__name__, direction)

    def get_team_contributor_serializer(
        self, profile_type: str, direction: str = "input"
    ):
        """
        Retrieve the TeamContributor serializer based on the profile type and direction.
        """
        serializers_map = self.TEAM_CONTRIBUTOR_SERIALIZER_MAPPING.get(
            profile_type, self.TEAM_CONTRIBUTOR_SERIALIZER_MAPPING["Default"]
        )
        return serializers_map.get(direction)
