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
            "external_links",
            "verification_stage",
            "role",
            "custom_role",
            "team_history_object",
            "visits",
            "is_promoted",
            "is_premium",
            "promotion",
        )


class GuestProfileUpdateSerializer(GuestProfileViewSerializer):
    """Serializer for updating guest profile data."""
