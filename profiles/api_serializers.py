import typing
from datetime import date, datetime

from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.http import QueryDict
from pydantic import parse_obj_as
from rest_framework import serializers

from clubs import errors as clubs_errors
from clubs.api import serializers as club_serializers
from clubs.services import ClubService
from clubs.models import Season
from external_links.serializers import ExternalLinksSerializer
from profiles import api_errors as profile_api_errors
from profiles import errors as profile_errors
from profiles import models
from profiles import serializers as profile_serializers
from profiles import services
from roles.definitions import PROFILE_TYPE_SHORT_MAP
from users.serializers import UserDataSerializer
from users.services import UserService
from utils.factories import utils
from voivodeships.serializers import VoivodeshipSerializer

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
    labels = serializers.SerializerMethodField()

    # fields related with profile (FK to profile)
    player_positions = profile_serializers.PlayerProfilePositionSerializer(
        many=True, required=False, read_only=True
    )
    player_video = profile_serializers.ProfileVideoSerializer(many=True, read_only=True)
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

    def get_labels(self, obj):
        """Override labels field to return only visible=True labels"""
        labels = ProfileLabelsSerializer(
            obj.labels.filter(visible=True),
            many=True,
            read_only=True,
        )
        return labels.data

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
            raise profile_api_errors.InvalidProfileRole

    def validate_team(self) -> None:
        """validate team id"""
        if team_id := self.initial_data.get("team_object_id"):  # noqa: E999
            if not clubs_service.team_exist(team_id):
                raise clubs_errors.TeamDoesNotExist

    def validate_club(self) -> None:
        """validate club id"""
        if club_id := self.initial_data.get("club_object_id"):
            if not clubs_service.club_exist(club_id):
                raise clubs_errors.ClubDoesNotExist

    def validate_team_history(self) -> None:
        """validate team history id"""
        if team_history_id := self.initial_data.get("team_history_id"):
            if not clubs_service.team_history_exist(team_history_id):
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
                raise profile_api_errors.IncompleteRequestBody(self.required_fields)
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
            raise profile_api_errors.UserAlreadyHasProfile

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
            raise profile_api_errors.InvalidProfileRole

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


class BaseProfileDataSerializer(serializers.Serializer):
    uuid = serializers.UUIDField(read_only=True)
    role = serializers.SerializerMethodField()
    verification_stage = profile_serializers.VerificationStageSerializer()
    is_main = serializers.SerializerMethodField(method_name="is_main_profile")

    def get_role(self, obj: models.PROFILE_TYPE) -> str:
        """get role by profile model"""
        return services.ProfileService.get_role_by_model(type(obj))

    def is_main_profile(self, obj: models.PROFILE_TYPE) -> bool:
        """Check if given profile is main profile for user"""
        role = self.get_role(obj)
        return role == obj.user.declared_role


class ProfileSearchSerializer(serializers.ModelSerializer):
    team = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()

    class Meta:
        model = models.User
        fields = (
            "role",
            "first_name",
            "last_name",
            "team",
            "age",
        )

    def get_age(self, obj: User) -> typing.Union[int, None]:
        """
        Retrieve the age for a given user from userpreferences.
        """
        return obj.userpreferences.age

    def get_team(self, obj: User) -> str:
        """
        Retrieve the team for a given profile.

        For PlayerProfile:
        - Checks if the player has a primary association with a team for the current season and round.
        - If such an association exists, it returns the team's display name along with its top parent league.

        For other profiles:
        - Checks for the primary team association irrespective of season or round.
        - If an association exists, returns the team's display name along with its top parent league.

        If neither of the above conditions is satisfied:
        - The function checks if the profile has a directly associated team object and returns its display name.

        If no association is found in any of the above conditions, the function returns "bez klubu"
        indicating that the profile does not have an associated team.
        """
        current_season = Season.define_current_season()
        current_round = Season.get_current_round()

        team_contrib = models.TeamContributor.objects.filter(
            profile_uuid=obj.profile.uuid,
            is_primary=True,
        ).first()

        if team_contrib:
            if (
                obj.role == "P"
                and team_contrib.round == current_round
                and team_contrib.team_history.filter(
                    league_history__season__name=current_season
                ).exists()
            ):
                team_history_instance = team_contrib.team_history.all().first()
                if team_history_instance:
                    return (
                        team_history_instance.team.display_team_with_league_top_parent
                    )

            else:
                team_history_instance = team_contrib.team_history.all().first()
                if team_history_instance:
                    return (
                        team_history_instance.team.display_team_with_league_top_parent
                    )

        if hasattr(obj.profile, "team_object") and obj.profile.team_object:
            return obj.profile.team_object.display_team_with_league_top_parent

        return "bez klubu"
