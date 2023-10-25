from profiles.models import ScoutProfile
from profiles.serializers_detailed.base_serializers import BaseProfileSerializer


class ScoutProfileViewSerializer(BaseProfileSerializer):
    """Serializer for retrieving scout profile data."""

    class Meta:
        model = ScoutProfile
        fields = (
            "slug",
            "user",
            "external_links",
            "profile_video",
            "verification_stage",
            "role",
        )


class ScoutProfileUpdateSerializer(ScoutProfileViewSerializer):
    """Serializer for updating scout profile data."""
