import logging
from typing import List, Optional, Union

from django.db.models import QuerySet
from pydantic import parse_obj_as
from rest_framework import serializers

from clubs.api.serializers import TeamHistoryBaseProfileSerializer
from clubs.errors import ClubDoesNotExist, TeamDoesNotExist
from clubs.models import Club, League
from clubs.services import ClubService
from external_links.serializers import ExternalLinksSerializer
from labels.services import LabelService
from labels.utils import fetch_all_labels
from premium.api.serializers import PromoteProfileProductSerializer
from profiles.api.errors import (
    InvalidProfileRole,
)
from profiles.api.serializers import (
    ProfileLabelsSerializer,
    ProfileVideoSerializer,
    VerificationStageSerializer,
)
from profiles.models import (
    PROFILE_TYPE,
    BaseProfile,
    PlayerProfile,
    TeamContributor,
)
from profiles.services import (
    PlayerProfilePositionService,
    PositionData,
    ProfileService,
    ProfileVisitHistoryService,
)
from roles.definitions import PROFILE_TYPE_SHORT_MAP
from transfers.models import ProfileTransferStatus
from transfers.api.serializers import (
    ProfileTransferRequestSerializer,
    ProfileTransferStatusSerializer,
)
from users.api.serializers import UserDataSerializer, UserSocialStatsSerializer

logger = logging.getLogger(__name__)


clubs_service: ClubService = ClubService()


class ClubSerializer(serializers.ModelSerializer):
    """Player profile club serializer"""

    picture = serializers.SerializerMethodField()

    class Meta:
        model = Club
        fields = (
            "id",
            "name",
            "picture",
        )

    def get_picture(self, obj: Club) -> Optional[str]:
        """Retrieve the absolute url of the club logo."""
        request = self.context.get("request")
        try:
            url = request.build_absolute_uri(obj.picture.url)
        except (ValueError, AttributeError):
            return None
        return url


class LeagueSerializer(serializers.ModelSerializer):
    """Player profile league serializer"""

    name = serializers.CharField(read_only=True)

    class Meta:
        model = League
        fields = ("id", "name")


class TeamContributorSerializer(serializers.ModelSerializer):
    """Team contributor serializer for user profile view"""

    from clubs.api.serializers import TeamHistoryBaseProfileSerializer

    team = serializers.SerializerMethodField()

    class Meta:
        model = TeamContributor
        fields = ("id", "round", "team")

    def get_team(self, obj: TeamContributor) -> dict:
        """Retrieve the team from the team_history object."""
        instance = obj.team_history.first()
        data = TeamHistoryBaseProfileSerializer(
            instance=instance, read_only=True, context=self.context
        )
        return data.data


class BaseProfileSerializer(serializers.ModelSerializer):
    """Base profile serializer for all profile types"""

    user = UserDataSerializer(partial=True, required=False)
    team_history_object = TeamHistoryBaseProfileSerializer(read_only=True)
    external_links = ExternalLinksSerializer(read_only=True)
    address = serializers.CharField(required=False)
    role = serializers.SerializerMethodField()
    labels = serializers.SerializerMethodField()
    verification_stage = VerificationStageSerializer(read_only=True)
    profile_video = serializers.SerializerMethodField()
    uuid = serializers.UUIDField(read_only=True)
    transfer_status = serializers.SerializerMethodField()
    transfer_requests = ProfileTransferRequestSerializer(many=True, read_only=True)
    visits = serializers.SerializerMethodField()
    promotion = PromoteProfileProductSerializer(read_only=True)
    social_stats = serializers.SerializerMethodField()

    def get_social_stats(self, obj: BaseProfile) -> dict:
        """Get social stats for the profile."""
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            if obj.user == request.user:
                hide_values = False
            else:
                hide_values = not self.context.get("premium_viewer", False)
        else:
            hide_values = True

        return UserSocialStatsSerializer(
            instance=obj.user,
            read_only=True,
            context={"hide_values": hide_values},
        ).data

    def get_visits(self, obj: BaseProfile) -> int:
        """Get profile visits from last month."""
        history_service = ProfileVisitHistoryService()
        return history_service.profile_visit_history_last_month(obj.user)

    def update(self, instance: PROFILE_TYPE, validated_data: dict):
        self.validate_data()

        if positions := self.initial_data.pop("player_positions", None):  # noqa: 5999
            player_position_service = PlayerProfilePositionService()
            # Parse the value as a list of PositionData objects
            positions_data = parse_obj_as(List[PositionData], positions)
            player_position_service.manage_positions(self.instance, positions_data)

        if user_data := validated_data.pop("user", None):  # noqa: 5999
            self.user = UserDataSerializer(
                instance=self.instance.user,
                data=user_data,
                partial=True,
                context=self.context,
            )
            if self.user.is_valid(raise_exception=True):
                self.user.save()

        if verification := self.initial_data.pop("verification_stage", None):
            verification_serializer = VerificationStageSerializer(
                instance=self.instance.verification_stage,
                data=verification,
                partial=True,
            )
            if verification_serializer.is_valid(raise_exception=True):
                verification_serializer.save()
        instance = super().update(instance, validated_data)
        if isinstance(instance, PlayerProfile) and "height" in validated_data:
            LabelService.assign_goalkeeper_height_label(instance.uuid)

        return instance

    def get_transfer_status(self, obj: BaseProfile) -> Optional[dict]:
        """Get transfer status by player profile."""
        if result := obj.meta.transfer_object:
            if isinstance(result, ProfileTransferStatus):
                serializer = ProfileTransferStatusSerializer(
                    result, required=False, context=self.context
                )
                return serializer.data

    def get_labels(self, obj: BaseProfile):
        """Override labels field to return both profile and user related labels"""
        label_context = self.context.get(
            "label_context", "profile"
        )  # Default to "profile"

        labels = ProfileLabelsSerializer(
            fetch_all_labels(obj, label_context=label_context),
            many=True,
            read_only=True,
        )
        return labels.data

    def get_role(self, obj: Union[QuerySet, PROFILE_TYPE]) -> str:
        """get role by model"""
        if isinstance(obj, QuerySet):
            obj = obj.first()
        return ProfileService.get_role_by_model(type(obj))

    @staticmethod
    def validate_role(role: str) -> None:
        """validate user role, raise exception if doesn't suits to the schema"""
        if role not in list(PROFILE_TYPE_SHORT_MAP.values()):
            raise InvalidProfileRole

    def validate_team(self) -> None:
        """validate team id"""
        if team_id := self.initial_data.get("team_object_id"):  # noqa: E999
            if not clubs_service.team_exist(team_id):
                raise TeamDoesNotExist

    def validate_club(self) -> None:
        """validate club id"""
        if club_id := self.initial_data.get("club_object_id"):
            if not clubs_service.team_exist(club_id):
                raise ClubDoesNotExist

    def validate_data(self) -> None:
        """validate ids of team, club and team history"""
        self.validate_team()
        self.validate_club()

    def to_representation(self, instance: PROFILE_TYPE) -> dict:
        """Hide verification stage from response if it's complete"""
        repr_dict = super().to_representation(instance)
        if "verification_stage" in repr_dict:
            if repr_dict["verification_stage"] and repr_dict["verification_stage"].get(
                "done"
            ):
                del repr_dict["verification_stage"]

        if repr_dict.get("external_links") is None:
            repr_dict["external_links"] = []

        # Special handling for 'team_history_object'
        if "team_history_object" in repr_dict and hasattr(instance, "uuid"):
            team_history_serializer_context = {
                "request": self.context.get("request"),
                "profile_uuid": instance.uuid,
            }

            # Check if there is a primary team contributor for the team history
            if hasattr(instance, "team_object") and instance.team_object:
                primary_contributor = instance.team_object.teamcontributor_set.filter(
                    is_primary=True, profile_uuid=instance.uuid
                ).first()

                if primary_contributor:
                    team_history_serializer = TeamHistoryBaseProfileSerializer(
                        instance.team_object,
                        context=team_history_serializer_context,
                    )
                    repr_dict["team_history_object"] = team_history_serializer.data
                else:
                    repr_dict["team_history_object"] = None
        else:
            repr_dict["team_history_object"] = None
        return repr_dict

    def get_profile_video(self, obj: PROFILE_TYPE) -> dict:
        """Override profile video field to return serialized data even if empty."""

        videos = ProfileVideoSerializer(
            instance=obj.user.user_video.all(),
            many=True,
            required=False,
            read_only=True,
        )
        return videos.data
