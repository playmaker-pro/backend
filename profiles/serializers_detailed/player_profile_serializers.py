import typing

from django.db.models import QuerySet
from rest_framework import serializers

from clubs.models import Club, League, Team
from external_links.serializers import ExternalLinksSerializer
from profiles.models import PROFILE_TYPE, PlayerPosition, PlayerProfile
from profiles.serializers import (
    ChoicesTuple,
    CoachLicenceSerializer,
    PlayerMetricsSerializer,
    PlayerProfilePositionSerializer,
    PlayerVideoSerializer,
    ProfileEnumChoicesSerializer,
)
from profiles.services import ProfileService
from users.models import User, UserPreferences
from users.serializers import UserPreferencesSerializer
from voivodeships.serializers import VoivodeshipSerializer


class PlayerProfileViewLeagueSerializer(serializers.ModelSerializer):
    """Player profile league serializer"""

    name = serializers.CharField(source="get_upper_parent_names", read_only=True)

    class Meta:
        model = League
        fields = ("id", "name", "is_parent")


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

    userpreferences = PlayerProfileViewUserPreferencesSerializer(
        required=False, partial=True
    )

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
            "role",
        )

    user = PlayerProfileViewUserDataSerializer(partial=True)
    team_object = PlayerProfileViewTeamSerializer(read_only=True)
    voivodeship_obj = VoivodeshipSerializer(read_only=True)
    external_links = ExternalLinksSerializer(required=False)
    address = serializers.CharField(required=False)
    player_positions = serializers.SerializerMethodField()
    player_video = PlayerVideoSerializer(many=True, read_only=True)
    licences = serializers.SerializerMethodField()
    transfer_status = serializers.SerializerMethodField()
    training_ready = serializers.SerializerMethodField()
    playermetrics = PlayerMetricsSerializer(read_only=True)
    role = serializers.SerializerMethodField()

    def get_player_positions(self, obj: PlayerProfile) -> typing.Optional[dict]:  # noqa
        """
        Get player positions by player profile.
        If no player positions return None (key still will be presented in response).
        """
        player_positions = PlayerProfileViewProfileEnumChoicesSerializer(
            required=False,
            model=PlayerProfile,
        )
        if not player_positions:
            return None

    def get_transfer_status(self, obj: PlayerProfile) -> typing.Optional[dict]:  # noqa
        """
        Get transfer status by player profile.
        If no transfer status return None (key still will be presented in response).
        """
        transfer_status = PlayerProfileViewProfileEnumChoicesSerializer(
            required=False,
            model=PlayerProfile,
        )
        if not transfer_status:
            return None

    def get_training_ready(self, obj: PlayerProfile) -> typing.Optional[dict]:  # noqa
        """
        Get trainings by player profile.
        If no trainings return None (key still will be presented in response).
        """
        trainings: dict = PlayerProfileViewProfileEnumChoicesSerializer(
            required=False,
            model=PlayerProfile,
        )
        if not trainings:
            return None

    def get_licences(self, obj: PlayerProfile) -> typing.Optional[dict]:  # noqa
        """
        Get licences by player profile.
        If no licences return None (key still will be presented in response).
        """
        licenses = CoachLicenceSerializer(many=True, required=False, data=obj)
        if not licenses:
            return None

    def get_role(self, obj: typing.Union[QuerySet, PROFILE_TYPE]) -> str:
        """get role by model"""
        if isinstance(obj, QuerySet):
            obj = obj.first()
        return ProfileService.get_role_by_model(type(obj))
