from django.contrib.auth import get_user_model
from django.db import models

from profiles.serializers_detailed.coach_profile_serializers import (
    CoachProfileUpdateSerializer,
    CoachProfileViewSerializer,
)
from profiles import serializers
from profiles.serializers_detailed.player_profile_serializers import (
    PlayerProfileViewSerializer,
)

User = get_user_model()


class VerificationObjectManager(models.Manager):
    def create_initial(self, owner: User):
        """Creates initial verifcation object for a profile based on current data."""
        if owner.is_club or owner.is_player or owner.coach():
            defaults = owner.profile.get_verification_data_from_profile()
            defaults["set_by"] = User.get_system_user()
            defaults["previous"] = None
            return super().create(**defaults)


class SerializersManager:
    SERIALIZER_MAPPING = {
        "PlayerProfile": PlayerProfileViewSerializer,
        "CoachProfile": CoachProfileViewSerializer,
        "CoachProfile_update": CoachProfileUpdateSerializer,
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
        """
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
