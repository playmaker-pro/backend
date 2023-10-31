from profiles.models import ClubProfile
from profiles.serializers_detailed.base_serializers import BaseProfileSerializer


class ClubProfileViewSerializer(BaseProfileSerializer):
    class Meta:
        model = ClubProfile
        fields = (
            "slug",
            "user",
            "labels",
            "club_role",
            "profile_video",
            "external_links",
            "labels",
            "role",
            "verification_stage",
            "team_history_object",
        )


class ClubProfileUpdateSerializer(ClubProfileViewSerializer):
    """Serializer for updating coach profile data."""
