import typing

from rest_framework import serializers

from profiles.models import PlayerPosition, PlayerProfile
from profiles.serializers import (
    ChoicesTuple,
    CoachLicenceSerializer,
    PlayerMetricsSerializer,
    PlayerProfilePositionSerializer,
    ProfileEnumChoicesSerializer,
    ProfileVideoSerializer,
)
from profiles.serializers_detailed.base_serializers import BaseProfileSerializer


class ProfileViePlayerPositionSerializer(serializers.ModelSerializer):
    """Player position serializer for user profile view"""

    class Meta:
        model = PlayerPosition
        fields = ("name", "shortcut")


class ProfileVIewPlayerProfilePositionSerializer(PlayerProfilePositionSerializer):
    """Player profile position serializer for user profile view"""

    player_position = ProfileViePlayerPositionSerializer()


class PlayerProfileViewProfileEnumChoicesSerializer(ProfileEnumChoicesSerializer):
    """Profile enum choices serializer for player profile view"""

    def to_representation(self, obj: typing.Union[ChoicesTuple, str]) -> dict:
        parsed_obj = obj
        if not obj:
            return {}
        if not isinstance(obj, ChoicesTuple):
            parsed_obj = self.parse(obj)
        return {"id": parsed_obj.id}

    def parse(self, _id) -> ChoicesTuple:
        """Get choices by model field and parse output"""
        _id = str(_id)
        choices = self.parse_dict(
            getattr(self.model, self.source).__dict__["field"].choices
        )

        if _id not in choices.keys():
            raise serializers.ValidationError(f"Invalid value: {_id}")

        value = choices[_id]
        return ChoicesTuple(_id, value)


class PlayerProfileViewSerializer(BaseProfileSerializer):
    class Meta:
        model = PlayerProfile
        fields = (
            "slug",
            "user",
            "team_object",
            "voivodeship_obj",
            "external_links",
            "address",
            "player_positions",
            "profile_video",
            "licences",
            "transfer_status",
            "height",
            "weight",
            "prefered_leg",
            "training_ready",
            "playermetrics",
            "role",
            "labels",
        )

    player_positions = ProfileVIewPlayerProfilePositionSerializer(
        many=True, required=False
    )
    licences = serializers.SerializerMethodField()
    transfer_status = ProfileEnumChoicesSerializer(
        required=False,
        model=PlayerProfile,
    )
    training_ready = ProfileEnumChoicesSerializer(
        required=False,
        model=PlayerProfile,
    )
    playermetrics = PlayerMetricsSerializer(read_only=True)
    role = serializers.SerializerMethodField()

    profile_video = serializers.SerializerMethodField()

    def get_profile_video(self, obj):
        """Override profile video field to return serialized data even if empty."""

        videos = ProfileVideoSerializer(
            instance=obj.user.user_video.all(),
            many=True,
            required=False,
            read_only=True,
        )
        return videos.data

    def get_licences(self, obj: PlayerProfile) -> typing.Optional[dict]:  # noqa
        """
        Get licences by player profile.
        If no licences return None (key still will be presented in response).
        """
        licenses = CoachLicenceSerializer(many=True, required=False, data=obj)
        return licenses.data if licenses.is_valid() else None
