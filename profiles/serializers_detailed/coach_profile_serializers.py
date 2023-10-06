from rest_framework import serializers

from external_links.serializers import ExternalLinksSerializer
from profiles.errors import InvalidCoachRoleException, InvalidFormationException
from profiles.models import FORMATION_CHOICES, CoachProfile, ProfileVideo
from profiles.serializers import ProfileEnumChoicesSerializer
from profiles.serializers_detailed.base_serializers import (
    BaseProfileSerializer,
    UserDataSerializer,
)


class ProfileVideoSerializer(serializers.ModelSerializer):
    thumbnail = serializers.CharField(
        source="get_youtube_thumbnail_url", read_only=True
    )

    class Meta:
        model = ProfileVideo
        fields = (
            "id",
            "url",
            "title",
            "description",
            "label",
            "thumbnail",
        )


class CoachProfileViewSerializer(BaseProfileSerializer):
    """Serializer for retrieving coach profile data."""

    class Meta:
        model = CoachProfile
        fields = (
            "slug",
            "user",
            "voivodeship_obj",
            "external_links",
            "coach_role",
            "training_ready",
            "formation",
            "profile_video",
        )

    coach_role = ProfileEnumChoicesSerializer(model=CoachProfile, required=False)
    training_ready = ProfileEnumChoicesSerializer(
        required=False,
        model=CoachProfile,
    )
    profile_video = serializers.SerializerMethodField()
    external_links = ExternalLinksSerializer(read_only=True)

    def get_profile_video(self, obj: CoachProfile) -> dict:
        """Override profile video field to return serialized data even if empty."""

        videos = ProfileVideoSerializer(
            instance=obj.user.user_video.all(),
            many=True,
            required=False,
            read_only=True,
        )
        return videos.data


class CoachProfileUpdateSerializer(CoachProfileViewSerializer):
    """Serializer for updating coach profile data."""

    def update(self, instance: CoachProfile, validated_data: dict) -> CoachProfile:
        """Update coach profile data. Overridden due to nested user data."""

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

        if coach_role := self.initial_data.get("coach_role"):
            if coach_role not in [role[0] for role in CoachProfile.COACH_ROLE_CHOICES]:
                raise InvalidCoachRoleException
            instance.coach_role = coach_role

        if formation := self.initial_data.get("formation"):
            if formation not in [formation[0] for formation in FORMATION_CHOICES]:
                raise InvalidFormationException
            instance.formation = formation

        super().update(instance, validated_data)

        return instance
