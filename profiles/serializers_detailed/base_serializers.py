from datetime import datetime
from typing import Optional

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.serializers import CitySerializer, CountrySerializer
from clubs.errors import ClubDoesNotExist, InvalidGender, TeamDoesNotExist
from clubs.models import Club, League, Team
from clubs.services import ClubService
from external_links.serializers import ExternalLinksSerializer
from profiles.errors import (
    InvalidProfileRole,
    LanguageDoesNotExistException,
    VoivodeshipDoesNotExistHTTPException,
    VoivodeshipWrongSchemaHTTPException,
)
from profiles.serializers import (
    CoachLicenceSerializer,
    CourseSerializer,
    LanguageSerializer,
    ProfileEnumChoicesSerializer,
)
from profiles.services import LanguageService
from roles.definitions import PROFILE_TYPE_SHORT_MAP
from users.models import User, UserPreferences
from voivodeships.exceptions import VoivodeshipDoesNotExist
from voivodeships.models import Voivodeships
from voivodeships.serializers import VoivodeshipSerializer
from voivodeships.services import VoivodeshipService

clubs_service: ClubService = ClubService()


class UserPreferencesSerializerDetailed(serializers.ModelSerializer):
    """User preferences serializer for user profile view"""

    class Meta:
        model = UserPreferences
        exclude = ("user", "id")

    age = serializers.IntegerField(read_only=True)
    localization = serializers.SerializerMethodField()
    spoken_languages = LanguageSerializer(many=True, required=False, allow_null=True)
    citizenship = CountrySerializer(many=True, required=False, allow_null=True)
    gender = ProfileEnumChoicesSerializer(
        model=UserPreferences, required=False, allow_null=True
    )
    licences = CoachLicenceSerializer(many=True, read_only=True, source="user.licences")
    courses = CourseSerializer(many=True, read_only=True, source="user.courses")

    def get_localization(self, obj: UserPreferences) -> dict:
        """Get city data. Return empty dict if city is not set"""
        if not obj.localization:
            return dict()
        serializer = CitySerializer(instance=obj.localization, required=False, allow_null=True)
        return serializer.data

    @staticmethod
    def validate_birth_date(value) -> datetime:
        """Check if birthdate is not in the future"""
        now = datetime.now().date()
        if value > now:
            raise ValidationError(detail="Birth date cannot be in the future")
        return value

    def update(self, instance: UserPreferences, validated_data) -> UserPreferences:
        """Update nested user preferences data"""
        if spoken_languages := validated_data.pop(  # noqa: 5999
            "spoken_languages", None
        ):

            language_service: LanguageService = LanguageService()
            for language_code in spoken_languages:
                try:
                    language_service.get_language_by_id(language_code)
                    instance.spoken_languages.set(spoken_languages)
                except LanguageDoesNotExistException:
                    pass

        if gender := validated_data.pop("gender", None):  # noqa: 5999
            if gender not in ["M", "K"]:
                raise InvalidGender
            instance.gender = gender

        super().update(instance, validated_data)
        return instance


class UserDataSerializer(serializers.ModelSerializer):
    """User data serializer for player profile view"""

    userpreferences = UserPreferencesSerializerDetailed(required=False, partial=True)

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

    def update(self, instance: User, validated_data: dict) -> User:
        """Update nested user data"""
        user_preferences = validated_data.pop("userpreferences", None)
        if user_preferences:
            user_preferences_serializer = UserPreferencesSerializerDetailed(
                instance=instance.userpreferences,
                data=user_preferences,
                partial=True,
            )
            if user_preferences_serializer.is_valid(raise_exception=True):
                user_preferences_serializer.save()
        super().update(instance, validated_data)
        return instance


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

    name = serializers.CharField(source="get_upper_parent_names", read_only=True)

    class Meta:
        model = League
        fields = ("id", "name", "is_parent")


class TeamSerializer(serializers.ModelSerializer):
    """Player profile team serializer"""

    club = ClubSerializer(required=False)
    league = LeagueSerializer(required=False)

    class Meta:
        model = Team
        fields = (
            "id",
            "name",
            "club",
            "league",
        )


class BaseProfileSerializer(serializers.ModelSerializer):
    """Base profile serializer for all profile types"""

    user = UserDataSerializer(partial=True, required=False)
    team_object = TeamSerializer(read_only=True)
    voivodeship_obj = VoivodeshipSerializer(read_only=True)
    external_links = ExternalLinksSerializer(required=False)
    address = serializers.CharField(required=False)

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

    def get_voivo(self) -> Optional[Voivodeships]:
        """Get voivodeship object from request data"""
        voivodeship_service: VoivodeshipService = VoivodeshipService()
        try:
            voivodeship = voivodeship_service.get_voivo_by_id(
                self.initial_data.get("voivodeship_obj").get("id")
            )
            return voivodeship
        except VoivodeshipDoesNotExist:
            raise VoivodeshipDoesNotExistHTTPException
        except AttributeError:
            raise VoivodeshipWrongSchemaHTTPException

    def validate_data(self) -> None:
        """validate ids of team, club and team history"""
        self.validate_team()
        self.validate_club()
