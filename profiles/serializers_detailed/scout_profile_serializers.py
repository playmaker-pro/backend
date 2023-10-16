from rest_framework import serializers

from external_links.serializers import ExternalLinksSerializer
from profiles.models import ScoutProfile
from profiles.serializers_detailed.coach_profile_serializers import (
    ProfileVideoSerializer,
)
from profiles.serializers_detailed.base_serializers import (
    BaseProfileSerializer,
    UserDataSerializer,
)


class ScoutProfileViewSerializer(BaseProfileSerializer):
    """Serializer for retrieving scout profile data."""

    class Meta:
        model = ScoutProfile
        fields = (
            "slug",
            "user",
            "voivodeship_obj",
            "external_links",
            "profile_video",
        )

    profile_video = serializers.SerializerMethodField()
    external_links = ExternalLinksSerializer(read_only=True)

    def get_profile_video(self, obj: ScoutProfile) -> dict:
        """Override profile video field to return serialized data even if empty."""

        videos = ProfileVideoSerializer(
            instance=obj.user.user_video.all(),
            many=True,
            required=False,
            read_only=True,
        )
        return videos.data


class ScoutProfileUpdateSerializer(ScoutProfileViewSerializer):
    """Serializer for updating scout profile data."""

    def update(self, instance: ScoutProfile, validated_data: dict) -> ScoutProfile:
        """Update scout profile data. Overridden due to nested user data."""
        self.validate_data()
        if user_data := validated_data.pop("user", None):  # noqa: 5999
            self.user = UserDataSerializer(
                instance=self.instance.user,
                data=user_data,
                partial=True,
            )
            if self.user.is_valid(raise_exception=True):
                self.user.save()

        if self.initial_data.get("voivodeship_obj"):
            voivo = self.get_voivo()
            instance.voivodeship_obj = voivo
            instance.save()
            self.initial_data.pop("voivodeship_obj")

        return instance
