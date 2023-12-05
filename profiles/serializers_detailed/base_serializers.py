import logging
from datetime import date
from typing import List, Optional, Union

from django.db.models import QuerySet
from django_countries import countries
from pydantic import parse_obj_as
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.consts import ChoicesTuple
from api.serializers import CitySerializer, CountrySerializer
from clubs.api.serializers import TeamHistoryBaseProfileSerializer
from clubs.errors import ClubDoesNotExist, InvalidGender, TeamDoesNotExist
from clubs.models import Club, League, Team
from clubs.services import ClubService, LeagueService
from external_links.serializers import ExternalLinksSerializer
from profiles.api.errors import (
    InvalidProfileRole,
    TransferStatusAlreadyExistsHTTPException,
)
from profiles.api.serializers import (
    CoachLicenceSerializer,
    CourseSerializer,
    LanguageSerializer,
    ProfileEnumChoicesSerializer,
    ProfileLabelsSerializer,
    ProfileVideoSerializer,
    VerificationStageSerializer,
)
from profiles.errors import (
    ExpectedIntException,
    InvalidCitizenshipListException,
    InvalidLanguagesListException,
    LanguageDoesNotExistException,
)
from profiles.models import (
    PROFILE_TYPE,
    BaseProfile,
    Language,
    ProfileTransferRequest,
    ProfileTransferStatus,
    TeamContributor,
)
from profiles.services import (
    LanguageService,
    PlayerProfilePositionService,
    PositionData,
    ProfileService,
    TransferStatusService,
)
from roles.definitions import (
    PROFILE_TYPE_SHORT_MAP,
    TRANSFER_STATUS_ADDITIONAL_INFO_CHOICES,
)
from users.models import User, UserPreferences

logger = logging.getLogger(__name__)


clubs_service: ClubService = ClubService()


class UserPreferencesSerializerDetailed(serializers.ModelSerializer):
    """User preferences serializer for user profile view"""

    class Meta:
        model = UserPreferences
        exclude = ("user", "id")

    age = serializers.IntegerField(read_only=True)
    localization = CitySerializer(required=False, allow_null=True)
    spoken_languages = LanguageSerializer(many=True, required=False, allow_null=True)
    citizenship = CountrySerializer(many=True, required=False, allow_null=True)
    gender = ProfileEnumChoicesSerializer(
        model=UserPreferences, required=False, allow_null=True
    )
    licences = CoachLicenceSerializer(many=True, read_only=True, source="user.licences")
    courses = CourseSerializer(many=True, read_only=True, source="user.courses")

    @staticmethod
    def validate_birth_date(value: date) -> date:
        """Check if birthdate is not in the future"""
        now = date.today()
        if value and value > now:
            raise ValidationError(detail="Birth date cannot be in the future")
        return value

    def validate_citizenship(self, citizenship: List[str]) -> List[str]:
        """Validate citizenship field"""
        if not isinstance(citizenship, list) or not all(
            [isinstance(el, str) for el in citizenship]
        ):
            raise InvalidCitizenshipListException(
                details="Citizenship must be a list of countries codes"
            )

        return [code for code in citizenship if code in countries]

    def validate_gender(self, value: str) -> str:
        """Validate gender field"""
        if value not in ["M", "K"]:
            raise InvalidGender
        return value

    def validate_spoken_languages(
        self, spoken_languages: List[Union[Language, str]]
    ) -> List[str]:
        """Validate spoken languages field"""
        is_list = isinstance(spoken_languages, list)

        if not is_list:
            raise InvalidLanguagesListException(
                details="Invalid languages list. Expected string "
                "values (language codes like: 'pl')"
            )

        language_service: LanguageService = LanguageService()

        for language_code in spoken_languages:
            if not isinstance(language_code, Language):
                try:
                    language: Language = language_service.get_language_by_code(
                        language_code.lower()
                    )
                    spoken_languages.append(language)
                except LanguageDoesNotExistException as e:
                    logger.error(e, exc_info=True)
                except ExpectedIntException as e:
                    logger.error(e, exc_info=True)
                spoken_languages.remove(language_code)

        return spoken_languages

    def update(self, instance: UserPreferences, validated_data) -> UserPreferences:
        """Update nested user preferences data"""
        if spoken_languages := validated_data.pop(  # noqa: 5999
            "spoken_languages", None
        ):
            instance.spoken_languages.set(
                [language.pk for language in spoken_languages]
            )

        return super().update(instance, validated_data)


class UserDataSerializer(serializers.ModelSerializer):
    """User data serializer for player profile view"""

    userpreferences = UserPreferencesSerializerDetailed(required=False, partial=True)
    picture = serializers.CharField(source="picture_url", read_only=True)
    last_activity = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "userpreferences",
            "picture",
            "last_activity",
        )
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
        return super().update(instance, validated_data)


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
    is_parent = serializers.SerializerMethodField()

    class Meta:
        model = League
        fields = ("id", "name", "is_parent")

    def get_is_parent(self, obj: League) -> bool:
        """Get is parent by league."""
        return obj.isparent


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


class PhoneNumberField(serializers.Field):
    """
    A custom field for handling phone numbers in the ManagerProfile serializer.

    This field is responsible for serializing and deserializing the phone number
    information (which includes 'dial_code' and 'agency_phone'). It handles the logic
    of combining these two separate fields into a single nested object for API
    representation, and it also processes incoming data for these fields
    in API requests.
    #  FIXME: lremkowicz: this is duplicated code, think about merging it with
    #  PhoneNumberField from ManagerProfileSerializer.
    """

    def to_representation(self, obj: ProfileTransferStatus) -> dict:
        """
        Converts the ManagerProfile instance's phone number information into
        a nested JSON object suitable for API output.
        """
        if not obj or (obj.dial_code is None and obj.phone_number is None):
            return None
        return {"dial_code": f"+{obj.dial_code}", "number": obj.phone_number}

    def to_internal_value(self, data: dict) -> dict:
        """
        Processes the incoming data for the phone number field.

        This method is responsible for parsing and validating the 'dial_code' and
        'number' from the incoming nested object. It ensures that partial updates
        are correctly handled by not overriding existing values with None when
        not provided.
        """
        internal_value = {}
        if "dial_code" in data:
            internal_value["dial_code"] = data["dial_code"]
        if "number" in data:
            internal_value["phone_number"] = data["number"]
        return internal_value


class ProfileTransferStatusSerializer(serializers.ModelSerializer):
    """Transfer status serializer for user profile view"""

    class Meta:
        model = ProfileTransferStatus
        fields = (
            "contact_email",
            "phone_number",
            "status",
            "additional_info",
            "league",
        )

    status = ProfileEnumChoicesSerializer(model=ProfileTransferStatus)
    additional_info = serializers.SerializerMethodField()
    league = serializers.PrimaryKeyRelatedField(
        queryset=LeagueService().get_highest_parents(), many=True
    )
    phone_number = PhoneNumberField(source="*", required=False)

    def get_additional_info(self, obj: ProfileTransferStatus) -> List[dict]:
        """
        Get additional info by transfer status. We have to write custom
        method because we have and ArrayField, which is not serializable by
        ProfileEnumChoicesSerializer.
        """
        data: list = []
        if obj.additional_info is None:
            return data
        for element in obj.additional_info:
            info = [
                ChoicesTuple(*transfer)
                for transfer in TRANSFER_STATUS_ADDITIONAL_INFO_CHOICES
                if transfer[0] == str(element)
            ]

            serializer = ProfileEnumChoicesSerializer(
                data=info,
                many=True,
            )
            serializer.is_valid()
            data.append(serializer.data)
        return data

    def update(self, instance: ProfileTransferStatus, validated_data: dict):
        """
        Due to fact that we overriden additional_info field we have to
        override update method to handle this field properly. When we
        used a SerializerMethodField, additional_info field is read only == it's not
        inside a validated_data. We have to pop it from initial_data.
        """
        if positions := self.initial_data.pop("additional_info", None):  # noqa: 5999
            validated_data["additional_info"] = positions
        return super().update(instance, validated_data)

    def create(self, validated_data: dict):
        """Create transfer status"""
        profile = self.context.get("profile")
        transfer_status = ProfileService().get_profile_transfer_status(profile)
        if transfer_status:
            raise TransferStatusAlreadyExistsHTTPException

        validated_data: dict = TransferStatusService.prepare_generic_type_content(
            validated_data, profile
        )
        instance = super().create(validated_data)
        return instance

    def to_representation(self, instance: ProfileTransferStatus):
        data = super().to_representation(instance)
        data["league"] = LeagueSerializer(instance=instance.league, many=True).data
        return data


class TeamContributorSerializer(serializers.ModelSerializer):
    """Team contributor serializer for user profile view"""

    team = serializers.SerializerMethodField()

    class Meta:
        model = TeamContributor
        fields = ("round", "team")

    def get_team(self, obj: TeamContributor) -> dict:
        """Retrieve the team from the team_history object."""
        instance = obj.team_history.first()
        data = TeamHistoryBaseProfileSerializer(instance=instance, read_only=True)
        return data.data


class ProfileTransferRequestSerializer(serializers.ModelSerializer):
    """Transfer request serializer for user profile view"""

    class Meta:
        model = ProfileTransferRequest
        fields = (
            "requesting_team",
            "gender",
            "status",
            "position",
            "number_of_trainings",
            "additional_info",
            "salary",
            "contact_email",
            "contact_phone",
        )

    requesting_team = TeamContributorSerializer()
    status = ProfileEnumChoicesSerializer(
        model=ProfileTransferRequest, required=False, allow_null=True
    )
    position = ProfileEnumChoicesSerializer(
        model=ProfileTransferRequest, required=False, allow_null=True
    )
    number_of_trainings = ProfileEnumChoicesSerializer(
        model=ProfileTransferRequest, required=False, allow_null=True
    )
    additional_info = ProfileEnumChoicesSerializer(
        model=ProfileTransferRequest, required=False, allow_null=True
    )
    salary = ProfileEnumChoicesSerializer(
        model=ProfileTransferRequest, required=False, allow_null=True
    )

    def create(self, validated_data):
        """Create transfer request"""

        profile = self.context.get("profile")
        transfer_status = ProfileService().get_profile_transfer_status(profile)
        if transfer_status:
            raise TransferStatusAlreadyExistsHTTPException

        validated_data: dict = TransferStatusService.prepare_generic_type_content(
            validated_data, profile
        )
        return super().create(validated_data)


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

        return super().update(instance, validated_data)

    def get_transfer_status(self, obj: BaseProfile) -> Optional[dict]:
        """Get transfer status by player profile."""
        result: list = obj.transfer_status_related.first()
        if result:
            serializer = ProfileTransferStatusSerializer(result, required=False)
            return serializer.data
        return None

    def get_labels(self, obj: BaseProfile):
        """Override labels field to return only visible=True labels"""
        labels = ProfileLabelsSerializer(
            obj.labels.filter(visible=True),
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
            if (
                hasattr(instance, "team_history_object")
                and instance.team_history_object
            ):
                primary_contributor = (
                    instance.team_history_object.teamcontributor_set.filter(
                        is_primary=True, profile_uuid=instance.uuid
                    ).first()
                )

                if primary_contributor:
                    team_history_serializer = TeamHistoryBaseProfileSerializer(
                        instance.team_history_object,
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
