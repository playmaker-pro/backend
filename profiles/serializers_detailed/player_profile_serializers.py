import typing

from rest_framework import serializers
from django.utils import translation
from django.utils.translation import gettext as _

from api.consts import ChoicesTuple
from api.i18n import I18nSerializerMixin
from profiles.api.serializers import (
    CoachLicenceSerializer,
    PlayerProfilePositionSerializer,
    ProfileEnumChoicesSerializer,
)
from profiles.models import PlayerMetrics, PlayerPosition, PlayerProfile
from profiles.serializers_detailed.base_serializers import BaseProfileSerializer


class ProfileViePlayerPositionSerializer(I18nSerializerMixin, serializers.ModelSerializer):
    """Player position serializer for user profile view with translation support"""

    class Meta:
        model = PlayerPosition
        fields = ("id", "name", "shortcut", "shortcut_pl")
        
    def to_representation(self, instance):
        """Override to return translated position names and appropriate shortcuts"""
        
        self._activate_context_language()
        
        # Get the current language from context
        current_language = self.context.get('language', 'pl')
        
        # Activate translation before calling parent to ensure model field translations work
        with translation.override(current_language):
            data = super().to_representation(instance)
            
            # The database contains Polish position names, so we translate them directly
            # This will use our existing translations from the .po files
            data['name'] = str(_(instance.name))
            
        # Return appropriate shortcut based on language
        if current_language == 'pl':
            data['shortcut'] = instance.shortcut_pl or instance.shortcut
        else:
            data['shortcut'] = instance.shortcut
            # Remove the Polish shortcut field for non-Polish languages
            data.pop('shortcut_pl', None)
            
        return data


class ProfileVIewPlayerProfilePositionSerializer(PlayerProfilePositionSerializer):
    """Player profile position serializer for user profile view"""

    player_position = ProfileViePlayerPositionSerializer()


class PlayerProfileViewProfileEnumChoicesSerializer(ProfileEnumChoicesSerializer):
    """Profile enum choices serializer for player profile view with translation support"""

    def to_representation(self, obj: typing.Union[ChoicesTuple, str]) -> dict:
        """Parse output with translation support - keep both id and translated name"""
        # Use parent class method which includes translation
        return super().to_representation(obj)

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


class PlayerMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerMetrics
        fields = (
            "pm_score",
            "season_score",
            "pm_score_state",
            "pm_score_change",
            "pm_score_history",
        )


class PlayerProfileViewSerializer(BaseProfileSerializer):
    class Meta:
        model = PlayerProfile
        fields = (
            "slug",
            "uuid",
            "user",
            "external_links",
            "player_positions",
            "profile_video",
            "transfer_status",
            "transfer_requests",
            "height",
            "weight",
            "prefered_leg",
            "training_ready",
            "playermetrics",
            "role",
            "labels",
            "verification_stage",
            "team_history_object",
            "visits",
            "is_promoted",
            "is_premium",
            "promotion",
            "social_stats",
        )

    player_positions = ProfileVIewPlayerProfilePositionSerializer(
        many=True, required=False
    )
    training_ready = ProfileEnumChoicesSerializer(
        required=False,
        model=PlayerProfile,
    )
    prefered_leg = ProfileEnumChoicesSerializer(
        required=False,
        model=PlayerProfile,
    )
    playermetrics = PlayerMetricsSerializer(read_only=True)
    role = serializers.SerializerMethodField()

    def get_licences(self, obj: PlayerProfile) -> typing.Optional[dict]:  # noqa
        """
        Get licences by player profile.
        If no licences return None (key still will be presented in response).
        """
        licenses = CoachLicenceSerializer(many=True, required=False, data=obj)
        return licenses.data if licenses.is_valid() else None

    def to_representation(self, instance):
        """Factory method to return appropriate serializer"""
        data = super().to_representation(instance)
        if (
            self.context.get("transfer_status")
            and instance.meta
            and instance.meta.transfer_object
            and instance.meta.transfer_status.is_anonymous
        ) or self.context.get("is_anonymous", False):
            uuid = instance.meta.transfer_status.anonymous_uuid
            data["slug"] = f"anonymous-{uuid}"
            data["uuid"] = uuid
            data["user"]["id"] = 0
            data["user"]["first_name"] = "Anonimowy"
            data["user"]["last_name"] = "profil"
            data["user"]["picture"] = None
            data["external_links"]["links"] = []
            data["profile_video"] = []
            data["transfer_status"]["contact_email"] = None
            data["transfer_status"]["phone_number"] = {
                "dial_code": None,
                "number": None,
            }
            data["team_history_object"] = None

        return data


class PlayerProfileUpdateSerializer(PlayerProfileViewSerializer):
    """Serializer for updating player profile data."""

    class Meta:
        model = PlayerProfile
        fields = (
            "slug",
            "user",
            "external_links",
            "player_positions",
            "profile_video",
            "transfer_status",
            "height",
            "weight",
            "prefered_leg",
            "training_ready",
            "playermetrics",
            "role",
            "labels",
            "verification_stage",
            "team_history_object",
        )

    player_positions = PlayerProfilePositionSerializer(
        many=True, required=False, read_only=True
    )
