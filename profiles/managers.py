from django.contrib.auth import get_user_model
from django.db import models

from profiles import serializers
from profiles.serializers_detailed.club_profile_serializers import (
    ClubProfileUpdateSerializer,
    ClubProfileViewSerializer,
)
from profiles.serializers_detailed.coach_profile_serializers import (
    CoachProfileUpdateSerializer,
    CoachProfileViewSerializer,
)
from profiles.serializers_detailed.player_profile_serializers import (
    PlayerProfileUpdateSerializer,
    PlayerProfileViewSerializer,
)
from profiles.serializers_detailed.scout_profile_serializers import (
    ScoutProfileUpdateSerializer,
    ScoutProfileViewSerializer,
)
from profiles.serializers_detailed.manager_profile_serializers import (
    ManagerProfileUpdateSerializer,
    ManagerProfileViewSerializer,
)

User = get_user_model()


class VerificationObjectManager(models.Manager):
    def create_initial(self, owner: User):
        """Creates initial verifcation object for a profile based on current data."""
        if owner.is_club or owner.is_player or owner.coach() or owner.scout():
            defaults = owner.profile.get_verification_data_from_profile()
            defaults["set_by"] = User.get_system_user()
            defaults["previous"] = None
            return super().create(**defaults)


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
        "ManagerProfile": ManagerProfileViewSerializer,
        "ManagerProfile_update": ManagerProfileUpdateSerializer,
    }
    PLAYER_PROFILE_TEAM_CONTRIBUTOR_SERIALIZERS = {
        "input": serializers.PlayerProfileTeamContributorInputSerializer,
        "output": serializers.PlayerTeamContributorSerializer,
    }

    OTHER_PROFILE_TEAM_CONTRIBUTOR_SERIALIZERS = {
        "input": serializers.OtherProfilesTeamContributorInputSerializer,
        "output": serializers.AggregatedTeamContributorSerializer,
    }

    TEAM_CONTRIBUTOR_SERIALIZER_MAPPING = {
        "PlayerProfile": PLAYER_PROFILE_TEAM_CONTRIBUTOR_SERIALIZERS,
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
