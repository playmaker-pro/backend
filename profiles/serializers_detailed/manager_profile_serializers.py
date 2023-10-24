from profiles.models import ManagerProfile
from profiles.serializers_detailed.base_serializers import BaseProfileSerializer


class ManagerProfileViewSerializer(BaseProfileSerializer):
    class Meta:
        model = ManagerProfile
        fields = (
            "slug",
            "user",
            "labels",
            "profile_video",
            "external_links",
            "labels",
            "role",
            "verification_stage",
            "agency_phone",
            "agency_email",
            "agency_transfermarkt_url",
            "agency_website_url",
            "agency_instagram_url",
            "agency_twitter_url",
            "agency_facebook_url",
            "agency_other_url",
        )


class ManagerProfileUpdateSerializer(ManagerProfileViewSerializer):
    """Serializer for updating manager profile data."""
