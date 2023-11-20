from profiles.models import GuestProfile
from profiles.serializers_detailed.base_serializers import BaseProfileSerializer


class GuestProfileViewSerializer(BaseProfileSerializer):
    """Serializer for retrieving guest profile data."""

    class Meta:
        model = GuestProfile
        fields = (
            "slug",
            "uuid",
            "user",
            "labels",
            "verification_stage",
            "role",
            "team_history_object",
        )


class GuestProfileUpdateSerializer(GuestProfileViewSerializer):
    """Serializer for updating guest profile data."""
