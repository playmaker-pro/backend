from django.contrib.auth import get_user_model
from django.db import models

from profiles.serializers_detailed.coach_profile_serializers import (
    CoachProfileUpdateSerializer,
    CoachProfileViewSerializer,
)
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

    def get_serializer(self, model_name: str):
        return self.SERIALIZER_MAPPING.get(model_name)
