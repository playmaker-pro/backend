import typing

from rest_framework import serializers

from clubs.models import League, Club, Team
from external_links.serializers import ExternalLinksSerializer
from profiles.models import PlayerPosition, PlayerProfile, PlayerProfilePosition
from profiles.serializers import (
    ChoicesTuple,
    CoachLicenceSerializer,
    PlayerProfilePositionSerializer,
    PlayerVideoSerializer,
    ProfileEnumChoicesSerializer,
    PlayerMetricsSerializer,
)
from users.models import User, UserPreferences
from users.serializers import UserPreferencesSerializer
from voivodeships.serializers import VoivodeshipSerializer


class PlayerProfileViewLeagueSerializer(serializers.ModelSerializer):
    """Player profile league serializer"""
    name = serializers.CharField(source="get_upper_parent_names", read_only=True)

    class Meta:
        model = League
        fields = (
            "id",
            "name",
            "is_parent"
        )


class PlayerProfileViewClubSerializer(serializers.ModelSerializer):
    """Player profile club serializer"""
    picture = serializers.SerializerMethodField()

    class Meta:
        model = Club
        fields = (
            "id",
            "name",
            "picture",
        )

    def get_picture(self, obj: Club) -> typing.Optional[str]:
        """Retrieve the absolute url of the club logo."""
        request = self.context.get("request")
        try:
            url = request.build_absolute_uri(obj.picture.url)
        except (ValueError, AttributeError):
            return None
        return url


class PlayerProfileViewTeamSerializer(serializers.ModelSerializer):
    """Player profile team serializer"""

    club = PlayerProfileViewClubSerializer(required=False)
    league = PlayerProfileViewLeagueSerializer(required=False)

    class Meta:
        model = Team
        fields = (
            "id",
            "name",
            "club",
            "league",
        )


class PlayerProfileViewUserPreferencesSerializer(UserPreferencesSerializer):
    """User preferences serializer for user profile view"""
    class Meta:
        model = UserPreferences
        exclude = ("user", "id")


class ProfileViePlayerPositionSerializer(serializers.ModelSerializer):
    """Player position serializer for user profile view"""

    class Meta:
        model = PlayerPosition
        fields = ("name", "shortcut")


class ProfileVIewPlayerProfilePositionSerializer(PlayerProfilePositionSerializer):
    """Player profile position serializer for user profile view"""

    player_position = ProfileViePlayerPositionSerializer()


class PlayerProfileViewUserDataSerializer(serializers.ModelSerializer):
    """User data serializer for player profile view"""

    userpreferences = PlayerProfileViewUserPreferencesSerializer(required=False, partial=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "userpreferences",
        ]
        depth = 1
        extra_kwargs = {
            "id": {"read_only": True},
        }


class PlayerProfileViewProfileEnumChoicesSerializer(ProfileEnumChoicesSerializer):
    """Profile enum choices serializer for player profile view"""

    def to_representation(self, obj: typing.Union[ChoicesTuple, str]) -> dict:
        result = super().to_representation(obj)
        return result.pop("name")


class PlayerProfileViewSerializer(serializers.ModelSerializer):
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
            "player_video",
            "licences",
            "transfer_status",
            "height",
            "weight",
            "prefered_leg",
            "training_ready",
            "playermetrics",
        )

    user = PlayerProfileViewUserDataSerializer(required=False, partial=True)
    team_object = PlayerProfileViewTeamSerializer(read_only=True)
    voivodeship_obj = VoivodeshipSerializer(read_only=True)
    external_links = ExternalLinksSerializer(required=False)
    address = serializers.CharField(required=False)
    player_positions = ProfileVIewPlayerProfilePositionSerializer(
        many=True, required=False
    )
    player_video = PlayerVideoSerializer(many=True, read_only=True)
    licences = CoachLicenceSerializer(many=True, required=False)
    transfer_status = PlayerProfileViewProfileEnumChoicesSerializer(
        required=False,
        model=PlayerProfile,
    )
    training_ready = PlayerProfileViewProfileEnumChoicesSerializer(
        required=False,
        model=PlayerProfile,
    )
    playermetrics = PlayerMetricsSerializer(read_only=True)
