import typing
from datetime import date, datetime
from functools import cached_property

from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.http import QueryDict
from pydantic import parse_obj_as
from rest_framework import serializers

from clubs import errors as clubs_errors
from clubs.api import serializers as club_serializers
from clubs.services import ClubService
from external_links.serializers import ExternalLinksSerializer
from profiles import errors as profile_errors
from profiles import services
from roles.definitions import PROFILE_TYPE_SHORT_MAP
from users.serializers import UserDataSerializer
from users.services import UserService
from utils.factories import utils
from voivodeships.serializers import VoivodeshipSerializer

from . import models
from . import serializers as profile_serializers

User = get_user_model()

clubs_service: ClubService = ClubService()
users_service: UserService = UserService()

TYPE_TO_SERIALIZER_MAPPING = {
    int: serializers.IntegerField(),
    float: serializers.FloatField(),
    bool: serializers.BooleanField(),
    type(None): serializers.BooleanField(allow_null=True),
    datetime: serializers.DateTimeField(),
    date: serializers.DateField(),
    list: serializers.ListField(),
    dict: serializers.DictField(),
    str: serializers.CharField(),
}
SERIALIZED_VALUE_TYPES = typing.Union[tuple(TYPE_TO_SERIALIZER_MAPPING.keys())]


class ProfileListSerializer(serializers.ListSerializer):
    exclude_fields: tuple = (
        "playermetrics",
        "player_video",
        "meta",
        "history",
    )

    def to_representation(self, data: list) -> list:
        """Override method to exclude fields from data"""
        return self.exclude_fields_from_response(super().to_representation(data))

    def exclude_fields_from_response(self, data: list) -> list:
        """Iterate through list objects and remove elements described in self.exclude_fields"""
        for obj in data:
            for key in self.exclude_fields:
                if key in obj.keys():
                    obj.pop(key, None)
        return data


class ProfileSerializer(serializers.Serializer):
    class Meta:
        list_serializer_class = ProfileListSerializer

    serialize_fields = ()  # if empty -> serialize all fields
    exclude_fields: tuple = (
        "event_log",
        "verification_id",
        "data_mapper_id",
        "team_club_league_voivodeship_ver",
        "external_links_id",
        "verification_stage_id",
        "history_id",
        "meta",
        "meta_updated",
        "birth_date",
        "position_alt",
        "position_raw_alt",
        "position_fantasy",
        "mapper_id",
        "country",
        "updated",
    )  # exclude fields from response
    required_fields = ()  # fields required as 'data'

    # sub-serializers
    user = UserDataSerializer(required=False, partial=True)
    team_object = club_serializers.TeamSerializer(read_only=True)
    team_history_object = club_serializers.TeamHistorySerializer(read_only=True)
    voivodeship_obj = VoivodeshipSerializer(read_only=True)
    history = profile_serializers.ProfileVisitHistorySerializer(
        required=False, partial=True
    )
    external_links = ExternalLinksSerializer(required=False)
    address = serializers.CharField(required=False)
    verification_stage = profile_serializers.VerificationStageSerializer(required=False)

    # fields related with profile (FK to profile)
    player_positions = profile_serializers.PlayerProfilePositionSerializer(
        many=True, required=False, read_only=True
    )
    player_video = profile_serializers.PlayerVideoSerializer(many=True, read_only=True)
    playermetrics = profile_serializers.PlayerMetricsSerializer(read_only=True)
    licences = profile_serializers.CoachLicenceSerializer(many=True, required=False)

    enums = (
        "transfer_status",
        "soccer_goal",
        "formation",
        "formation_alt",
        "prefered_leg",
        "card",
        "training_ready",
        "agent_status",
        "coach_role",
        "referee_role",
        "licence",
    )

    # meta fields
    player_stats = serializers.SerializerMethodField(read_only=True)
    role = serializers.SerializerMethodField()

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        if self.instance:
            self.model: models.PROFILE_TYPE = (
                type(self.instance[0])
                if isinstance(self.instance, (QuerySet, list))
                else type(self.instance)
            )

    @property
    def data(self) -> dict:
        """return whole serialized object"""
        return self.to_representation()

    def to_representation(
        self, obj: models.PROFILE_TYPE = None, *args, **kwargs
    ) -> dict:
        """serialize each attr of given model into json"""
        obj = obj or self.instance
        ret = super().to_representation(obj)
        fields: list[str] = self.serialize_fields or obj.__dict__.keys()

        for field_name in fields:
            if field_name.startswith("_"):
                continue

            field_value = getattr(obj, field_name)

            if field_name in self.enums and field_value:
                serializer_field = profile_serializers.ProfileEnumChoicesSerializer(
                    required=False,
                    model=self.model,
                    source=field_name,
                )
            else:
                serializer_field: serializers.Field = self.get_serializer_field(
                    field_value
                )
            ret[field_name] = serializer_field.to_representation(field_value)

            if not isinstance(obj, models.PlayerProfile):
                ret.pop("player_stats", None)

        for field_name in self.exclude_fields:
            ret.pop(field_name, None)

        return ret

    def get_serializer_field(
        self, field_value: SERIALIZED_VALUE_TYPES
    ) -> serializers.Field:
        """parse serialized fields"""
        return TYPE_TO_SERIALIZER_MAPPING.get(
            type(field_value), serializers.CharField()
        )

    def get_role(self, obj: typing.Union[QuerySet, models.PROFILE_TYPE]) -> str:
        """get role by model"""
        if isinstance(obj, QuerySet):
            obj = obj.first()
        return services.ProfileService.get_role_by_model(type(obj))

    def save(self) -> None:
        """This serializer should not be able to save anything"""
        raise profile_errors.SerializerError(
            f"{self.__class__.__name__} should not be able to save anything!"
        )

    def validate_role(self, role: str) -> None:
        """validate user role, raise exception if doesn't suits to the schema"""
        if role not in list(PROFILE_TYPE_SHORT_MAP.values()):
            raise profile_errors.InvalidProfileRole

    def validate_team(self) -> None:
        """validate team id"""
        if team_id := self.initial_data.get("team_object_id"):  # noqa: E999
            if not clubs_service.team_exist(team_id):
                raise clubs_errors.TeamDoesNotExist

    def validate_club(self) -> None:
        """validate club id"""
        if club_id := self.initial_data.get("club_object_id"):
            if not clubs_service.team_exist(club_id):
                raise clubs_errors.ClubDoesNotExist

    def validate_team_history(self) -> None:
        """validate team history id"""
        if team_history_id := self.initial_data.get("club_object_id"):
            if not clubs_service.team_exist(team_history_id):
                raise clubs_errors.TeamHistoryDoesNotExist

    def validate_data(self) -> None:
        """validate ids of team, club and team history"""
        self.validate_team()
        self.validate_club()
        self.validate_team_history()

    def initial_validation(self, data: typing.Dict) -> dict:
        """Validate serializer input (data **kw)"""
        for field in self.required_fields:
            if not data or field not in data.keys():
                raise profile_errors.IncompleteRequestBody(self.required_fields)
        return data.dict() if isinstance(data, QueryDict) else data

    def get_player_stats(self, obj: models.PROFILE_TYPE) -> dict:
        """
        Get player summary stats on players catalog
        Solution is temporarily mocked, full logic will be delivered soon
        """
        if isinstance(obj, models.PlayerProfile):
            ...  # TODO(bartnyk): create logic for stats based on metrics, preferably in ProfileService

            return {
                "last_goals_count": utils.get_random_int(0, 8),
                "matches": utils.get_random_int(5, 500),
                "avg_minutes": utils.get_random_int(0, 90),
            }  # temp mocked


class CreateProfileSerializer(ProfileSerializer):
    user_id = serializers.IntegerField()
    uuid = serializers.CharField(read_only=True)
    serialize_fields = (
        "user_id",
        "uuid",
        "role",
    )
    required_fields = ("role",)

    def __init__(self, *args, **kwargs) -> None:
        kwargs["data"] = self.initial_validation(kwargs.get("data"))
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data: dict) -> dict:
        """Get user directly from request auth (requestor)"""
        if user := self.context.get("requestor"):
            data["user_id"] = user.pk
            return super().to_internal_value(data)
        else:
            raise serializers.ValidationError(
                {"error": "Unable to define owner of a request."}
            )

    def to_representation(self, *args, **kwargs) -> dict:
        ret = super(ProfileSerializer, self).to_representation(self.instance)
        return {key: ret[key] for key in self.serialize_fields}

    def validate_user(self):
        """Validate user_is was given and user exist"""
        user_obj: User = self.context.get("requestor")

        if users_service.user_has_profile(user_obj, self.model):
            raise profile_errors.UserAlreadyHasProfile

    def handle_positions(self, positions_data: list) -> None:
        """Handles the creation of player positions."""
        positions_service = services.PlayerProfilePositionService()
        # Parse the value as a list of PositionData objects
        positions_data = parse_obj_as(
            typing.List[services.PositionData], positions_data
        )
        positions_service.manage_positions(self.instance, positions_data)

    def validate_data(self) -> None:
        """Validate data"""
        super().validate_data()
        self.validate_user()

    def save(self) -> None:
        """create profile and set role for given user, need to validate data first"""
        try:
            self.model = services.ProfileService.get_model_by_role(
                self.initial_data.pop("role")
            )
        except ValueError:
            raise profile_errors.InvalidProfileRole

        self.validate_data()
        positions_data = self.initial_data.pop("player_positions", None)
        self.instance = self.model.objects.create(**self.initial_data)

        if positions_data and isinstance(self.instance, models.PlayerProfile):
            self.handle_positions(positions_data)


class UpdateProfileSerializer(ProfileSerializer):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.user = self.instance.user

    read_only_fields = (
        "user_id",
        "history_id",
        "mapper_id",
        "verification_id",
        "data_mapper_id",
        "external_links_id",
        "address_id",
    )  # read-only fields, should not be able to update

    def update_fields(self) -> None:
        """Update fields given in payload"""
        if user_data := self.initial_data.pop("user", None):
            self.user = UserDataSerializer(
                instance=self.instance.user,
                data=user_data,
                partial=True,
            )
            if self.user.is_valid(raise_exception=True):
                self.user.save()

        if verification := self.initial_data.pop("verification_stage", None):
            verification_serializer = profile_serializers.VerificationStageSerializer(
                instance=self.instance.verification_stage,
                data=verification,
                partial=True,
            )
            if verification_serializer.is_valid(raise_exception=True):
                verification_serializer.save()

        if history_data := self.initial_data.pop("history", None):  # noqa: E999
            self.history = profile_serializers.ProfileVisitHistorySerializer(
                instance=self.instance.history, data=history_data, partial=True
            )
            if self.history.is_valid(raise_exception=True):
                self.history.save()

        for attr, value in self.initial_data.items():
            if attr in self.read_only_fields:
                continue

            if attr == "player_positions":
                player_position_service = services.PlayerProfilePositionService()
                # Parse the value as a list of PositionData objects
                positions_data = parse_obj_as(typing.List[services.PositionData], value)
                player_position_service.manage_positions(self.instance, positions_data)
            elif hasattr(self.instance, attr):
                setattr(self.instance, attr, value)

    def save(self) -> None:
        """If data is valid, update fields and save profile instance"""
        self.validate_data()
        self.update_fields()
        self.instance.save()


class ProfileLabelsSerializer(serializers.Serializer):
    label_name = serializers.CharField(max_length=25)
    label_description = serializers.CharField(max_length=200)
    season_name = serializers.CharField(max_length=9)
    icon = serializers.CharField(max_length=200)


class BaseProfileDataSerializer(ProfileSerializer):
    def to_representation(
        self, obj: typing.Optional[models.PROFILE_TYPE] = None, *args, **kwargs
    ) -> dict:
        """Override custom to_representation to return just uuid + role"""
        obj = obj or self.instance

        # Use the VerificationStageSerializer to serialize the verification_stage field
        verification_stage_serializer = profile_serializers.VerificationStageSerializer(
            instance=obj.verification_stage
        )
        return {
            "uuid": obj.uuid,
            "role": services.ProfileService.get_role_by_model(type(obj)),
            "verification_stage": verification_stage_serializer.data,
        }
