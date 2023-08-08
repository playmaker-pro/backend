import typing
from datetime import date, datetime
from rest_framework import serializers
from django.contrib.auth import get_user_model
from clubs import errors as clubs_errors
from clubs.services import ClubService
from profiles import errors as profile_errors
from profiles.services import ProfileService, PlayerProfilePositionService
from . import models
from roles.definitions import PROFILE_TYPE_SHORT_MAP
from users.services import UserService
from pydantic import parse_obj_as
from profiles.services import PositionData

User = get_user_model()

profiles_service: ProfileService = ProfileService()
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


class ProfileSerializer(serializers.Serializer):
    serialize_fields = []  # if empty -> serialize all fields
    required_fields = []  # fields required as 'data'

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.profile_role: str = self.get_role()
        self.model: models.PROFILE_TYPE = self.define_model()

    @property
    def data(self) -> dict:
        """return whole serialized object"""
        return self.to_representation()

    def to_representation(self, *args, **kwargs) -> dict:
        """serialize each attr of given model into json"""
        ret = {}
        fields: list[str] = self.serialize_fields or self.instance.__dict__
        for field_name in fields:
            if field_name.startswith("_"):
                continue

            field_value = getattr(self.instance, field_name)
            serializer_field: serializers.Field = self.get_serializer_field(field_value)
            ret[field_name] = serializer_field.to_representation(field_value)

        ret["role"] = self.profile_role

        # TODO: new serializers for profiles-related models
        #  https://gitlab.com/playmaker1/webapp/-/commit/6fa060ad101198064425d71f1d11aa3d3a892678.

        # Only serialize player_positions if the profile is a PlayerProfile
        if isinstance(self.instance, models.PlayerProfile):
            ret["player_positions"] = PlayerProfilePositionSerializer(
                self.instance.player_positions.order_by("-is_main"), many=True
            ).data
        return ret

    def get_serializer_field(
        self, field_value: SERIALIZED_VALUE_TYPES
    ) -> serializers.Field:
        """parse serialized fields"""
        return TYPE_TO_SERIALIZER_MAPPING.get(
            type(field_value), serializers.CharField()
        )

    def get_role(self) -> str:
        """get and pop role from data"""
        return profiles_service.get_role_by_model(type(self.instance))

    def save(self) -> None:
        """This serializer should not be able to save anything"""
        raise profile_errors.SerializerError(
            f"{self.__class__.__name__} should not be able to save anything!"
        )

    def define_model(self) -> models.PROFILE_TYPE:
        """Define profile model based on role shortcut"""
        return profiles_service.get_model_by_role(self.profile_role)

    def validate_role(self, role: str) -> None:
        """validate user role, raise exception if doesn't suits to the schema"""
        if role not in list(PROFILE_TYPE_SHORT_MAP.values()):
            raise profile_errors.InvalidProfileRole()

    def validate_team(self) -> None:
        """validate team id"""
        if team_id := self.initial_data.get("team_object_id"):
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

    def initial_validation(self, data: typing.Dict):
        """Validate serializer input (data **kw)"""
        for field in self.required_fields:
            if not data or field not in data.keys():
                raise profile_errors.IncompleteRequestData(self.required_fields)
            return data


class CreateProfileSerializer(ProfileSerializer):
    user_id = serializers.IntegerField()
    role = serializers.CharField()
    serialize_fields = ["user_id", "uuid"]
    required_fields = ["user_id", "role"]

    def __init__(self, *args, **kwargs) -> None:
        kwargs["data"] = self.initial_validation(kwargs.get("data"))
        super().__init__(*args, **kwargs)

    def get_role(self) -> str:
        """get and pop role from data"""
        try:
            role: str = self.initial_data.get("role")
        except KeyError:
            raise profile_errors.InvalidProfileRole

        self.validate_role(role)
        return role

    def validate_user(self):
        """Validate user_is was given and user exist"""
        user_id: int = self.initial_data.get("user_id")
        user_obj: User = users_service.get_user(user_id)

        if not user_id or not user_obj:
            raise profile_errors.InvalidUser

        if users_service.user_has_profile(user_obj, self.model):
            raise profile_errors.UserAlreadyHasProfile

    def handle_positions(self, positions_data: list) -> None:
        """Handles the creation of player positions."""
        positions_service = PlayerProfilePositionService()
        # Parse the value as a list of PositionData objects
        positions_data = parse_obj_as(typing.List[PositionData], positions_data)
        positions_service.manage_positions(self.instance, positions_data)

    def validate_data(self) -> None:
        """Validate data"""
        super().validate_data()
        self.validate_user()

    def save(self) -> None:
        """create profile and set role for given user, need to validate data first"""
        self.validate_data()
        self.initial_data.pop("role")
        positions_data = self.initial_data.pop("player_positions", None)
        self.instance = self.model.objects.create(**self.initial_data)

        if positions_data and isinstance(self.instance, models.PlayerProfile):
            self.handle_positions(positions_data)


class UpdateProfileSerializer(ProfileSerializer):
    uuid = serializers.UUIDField()
    required_fields = ["uuid"]

    def __init__(self, *args, **kwargs) -> None:
        data = self.initial_validation(kwargs.get("data"))
        uuid = data.get("uuid", "")

        if not profiles_service.is_valid_uuid(uuid):
            raise profile_errors.InvalidUUID

        kwargs["instance"]: models.PROFILE_TYPE = profiles_service.get_profile_by_uuid(
            uuid
        )
        super().__init__(*args, **kwargs)

    def update_fields(self) -> None:
        """Update fields given in payload"""
        for attr, value in self.initial_data.items():
            if attr == "player_positions":
                player_position_service = PlayerProfilePositionService()
                # Parse the value as a list of PositionData objects
                positions_data = parse_obj_as(typing.List[PositionData], value)
                player_position_service.manage_positions(self.instance, positions_data)
            elif hasattr(self.instance, attr):
                setattr(self.instance, attr, value)

    def save(self) -> None:
        """If data is valid, update fields and save profile instance"""
        self.validate_data()
        self.update_fields()
        self.instance.save()


class ProfileEnumListSerializer(serializers.ListSerializer):
    """List serializer for ClubProfile roles"""

    def to_internal_value(self, data: typing.List[tuple]) -> typing.List[dict]:
        return [{"id": value[0], "name": value[1]} for value in data]


class ProfileEnumChoicesSerializer(serializers.Serializer):
    """Serializer for ClubProfile roles"""

    id = serializers.CharField()
    name = serializers.CharField(read_only=True)

    class Meta:
        list_serializer_class = ProfileEnumListSerializer


class PlayerProfilePositionSerializer(serializers.ModelSerializer):
    """
    Serializer for the player's profile position, including the name of the position
    and whether it is the main position.
    """

    position_name = serializers.CharField(source="player_position.name", read_only=True)

    class Meta:
        model = models.PlayerProfilePosition
        fields = ["player_position", "position_name", "is_main"]

    def to_representation(self, instance) -> typing.Dict[str, typing.Any]:
        """
        Converts the instance into a dictionary format.
        """
        ret = super().to_representation(instance)

        return {"player_position": ret["player_position"], "is_main": ret["is_main"]}


class PlayerPositionSerializer(serializers.ModelSerializer):
    """
    Serializer for the player's position, including the ID and name of the position.
    """

    class Meta:
        model = models.PlayerPosition
        fields = ["id", "name"]


class LicenceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LicenceType
        fields = "__all__"
