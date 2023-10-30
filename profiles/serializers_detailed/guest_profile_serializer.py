from profiles.models import GuestProfile
from profiles.serializers_detailed.base_serializers import BaseProfileSerializer


class GuestProfileViewSerializer(BaseProfileSerializer):
    """Serializer for retrieving guest profile data."""

    class Meta:
        model = GuestProfile
        fields = (
            "slug",
            "user",
            "labels",
            "verification_stage",
            "role",
        )


class GuestProfileUpdateSerializer(GuestProfileViewSerializer):
    """Serializer for updating guest profile data."""
