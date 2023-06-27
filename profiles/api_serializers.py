from datetime import date
from typing import List, Type
from rest_framework import serializers
from django.contrib.auth import get_user_model
from clubs.errors import TeamDoesNotExist, ClubDoesNotExist, TeamHistoryDoesNotExist
from clubs.services import ClubService
from profiles.erros import UserAlreadyHasProfile, InvalidUserRole, InvalidUser
from profiles.services import ProfileService
from .models import PROFILES, PROFILE_TYPE
from roles.definitions import PROFILE_TYPE_SHORT_MAP
from users.services import UserService

User = get_user_model()

profiles_service: ProfileService = ProfileService()
clubs_service: ClubService = ClubService()
users_service: UserService = UserService()


class ProfileSerializer(serializers.Serializer):
    def __init__(
        self,
        instance: PROFILE_TYPE = None,
        model: Type[PROFILE_TYPE] = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(instance, *args, **kwargs)

        self.user_obj: User = self.get_user()
        self.user_role: str = self.get_role()
        self.model: Type[PROFILE_TYPE] = model or self.define_model()
        if not self.model:
            raise AttributeError(f"No model defined, options: {PROFILES}")

    def define_model(self) -> Type[PROFILE_TYPE]:
        return profiles_service.get_model_by_role(self.user_role)

    def get_user(self) -> User:
        """get user with given user_id, raise exception if no user_id or user doesn't exist"""
        try:
            user_id: int = self.initial_data.get("user_id")
        except AttributeError:
            raise InvalidUser()

        user_obj: User = users_service.get_user(user_id)
        if not user_obj:
            raise InvalidUser()

        return user_obj

    @property
    def data(self) -> dict:
        """return whole serialized object"""
        return self.to_representation()

    def to_representation(self, fields_pool: List[str] = None) -> dict:
        """serialize each attr of given model into json"""
        ret = {}
        fields: list[str] = fields_pool or self.instance.__dict__
        for field_name in fields:
            if field_name.startswith("_") or field_name == "_state":
                continue

            field_value = getattr(self.instance, field_name)
            serializer_field = self.get_serializer_field(field_value)
            ret[field_name] = serializer_field.to_representation(field_value)

        ret["role"] = self.user_role
        return ret

    def get_serializer_field(self, field_value) -> serializers.Field:
        """parse serialized fields"""
        if isinstance(field_value, str):
            return serializers.CharField()
        elif isinstance(field_value, int):
            return serializers.IntegerField()
        elif isinstance(field_value, float):
            return serializers.FloatField()
        elif isinstance(field_value, bool):
            return serializers.BooleanField()
        elif isinstance(field_value, date):
            return serializers.DateTimeField()
        return serializers.CharField()

    def validate_team(self) -> None:
        """validate team id"""
        if team_id := self.initial_data.get("team_object_id"):
            if not clubs_service.team_exist(team_id):
                raise TeamDoesNotExist()

    def validate_club(self) -> None:
        """validate club id"""
        if club_id := self.initial_data.get("club_object_id"):
            if not clubs_service.team_exist(club_id):
                raise ClubDoesNotExist()

    def validate_team_history(self) -> None:
        """validate team history id"""
        if team_history_id := self.initial_data.get("club_object_id"):
            if not clubs_service.team_exist(team_history_id):
                raise TeamHistoryDoesNotExist()

    def get_role(self) -> str:
        """get and pop role from data"""
        try:
            role: str = self.initial_data.pop("role")
        except KeyError:
            raise InvalidUserRole()

        self.validate_role(role)
        return role

    def validate_role(self, role) -> None:
        """validate user role, raise exception if doesn't suits to the schema"""
        if role not in list(PROFILE_TYPE_SHORT_MAP.values()):
            raise InvalidUserRole()

    def validate_data(self) -> None:
        """validate ids of team, club and team history"""
        self.validate_team()
        self.validate_club()
        self.validate_team_history()

    def validate_user_has_no_profile(
        self,
    ) -> None:
        """Check if user has profile, if so - raise exception"""
        if users_service.user_has_profile(self.user_obj, self.model):
            raise UserAlreadyHasProfile()

    def refresh_instance(self) -> None:
        """Refresh profile instance before serialize"""
        self.instance: PROFILE_TYPE = self.model.objects.get(user=self.user_obj)

    def save(self) -> None:
        """This serializer should not be able to save anything"""
        raise NotImplementedError()


class CreateProfileSerializer(ProfileSerializer):
    def save(self) -> None:
        """create profile and set role for given user, need to validate data first"""
        self.validate_user_has_no_profile()
        self.validate_data()
        profiles_service.create_profile_with_initial_data(self.model, self.initial_data)
        self.refresh_instance()

    @property
    def data(self) -> dict:
        """
        return serialized object, just user_id and role
        {user_id: .., role: ..}
        """
        fields = ["user_id"]
        return self.to_representation(fields)
