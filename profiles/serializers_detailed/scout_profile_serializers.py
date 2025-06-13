from profiles.models import ScoutProfile
from profiles.serializers_detailed.base_serializers import BaseProfileSerializer


class ScoutProfileViewSerializer(BaseProfileSerializer):
    """Serializer for retrieving scout profile data."""

    class Meta:
        model = ScoutProfile
        fields = (
            "slug",
            "uuid",
            "user",
            "external_links",
            "profile_video",
            "verification_stage",
            "role",
            "team_history_object",
            "visits",
            "is_promoted",
            "is_premium",
            "promotion",
            "social_stats",
        )


class ScoutProfileUpdateSerializer(ScoutProfileViewSerializer):
    """Serializer for updating scout profile data."""
