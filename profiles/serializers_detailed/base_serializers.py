import logging
import typing
from datetime import date
from typing import Any, List, Optional, Union

from django.db.models import QuerySet
from django_countries import countries
from pydantic import parse_obj_as
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty
from rest_framework.relations import PrimaryKeyRelatedField

from api.consts import ChoicesTuple
from api.serializers import CitySerializer, CountrySerializer
from clubs.api.serializers import TeamHistoryBaseProfileSerializer
from clubs.errors import InvalidGender
from clubs.models import Club, League
from clubs.services import ClubService, LeagueService
from external_links.serializers import ExternalLinksSerializer
from labels.services import LabelService
from labels.utils import fetch_all_labels
from premium.api.serializers import PromoteProfileProductSerializer
from profiles.api.errors import (
    InvalidProfileRole,
    NotAOwnerOfTheTeamContributorHTTPException,
    PhoneNumberMustBeADictionaryHTTPException,
    TransferRequestAlreadyExistsHTTPException,
    TransferStatusAlreadyExistsHTTPException,
)
from profiles.api.serializers import (
    CoachLicenceSerializer,
    CourseSerializer,
    LanguageSerializer,
    PlayerPositionSerializer,
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
    PlayerPosition,
    PlayerProfile,
    ProfileTransferRequest,
    ProfileTransferStatus,
    TeamContributor,
)
from profiles.serializers_detailed.mixins import EmailUpdateMixin, PhoneNumberMixin
from profiles.services import (
    LanguageService,
    PlayerProfilePositionService,
    PositionData,
    ProfileService,
    ProfileVisitHistoryService,
    TransferStatusService,
)
from roles.definitions import (
    TRANSFER_BENEFITS_CHOICES,
    TRANSFER_SALARY_CHOICES,
    TRANSFER_STATUS_ADDITIONAL_INFO_CHOICES,
    TRANSFER_TRAININGS_CHOICES,
)
from users.api.serializers import UserSocialStatsSerializer
from users.models import User, UserPreferences

logger = logging.getLogger(__name__)


clubs_service: ClubService = ClubService()
label_service: LabelService = LabelService()


class SharedValidatorsMixin:
    """Mixing for shared methods."""

    def validate_phone_number(self, phone_number: dict) -> dict:  # noqa
        """Validate phone number field. Running when creating object."""
        if not isinstance(phone_number, dict):
            raise ValidationError(detail="Phone number must be a dict")
        if dial_code := phone_number.get("dial_code"):  # noqa: 5999
            try:
                int(dial_code)
            except ValueError:
                raise ValidationError(detail="Dial code must be an integer")
        return phone_number

    def validate_additional_info(self, additional_info: list) -> list:  # noqa
        """Validate additional info field"""
        if not isinstance(additional_info, list) or not all(
            (isinstance(el, int) for el in additional_info)
        ):
            raise ValidationError(detail="Additional info must be a list of integers")
        return additional_info


class UserPreferencesSerializerDetailed(serializers.ModelSerializer):
    """User preferences serializer for user profile view"""

    class Meta:
        model = UserPreferences
        exclude = ("user", "id", "phone_number", "contact_email", "dial_code")

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
        if not isinstance(citizenship, list) or not all([
            isinstance(el, str) for el in citizenship
        ]):
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
        if profile := self.context.get("profile"):
            profile_type = profile.__class__.__name__
            profile_uuid = profile.uuid
        else:
            profile_uuid = self.context.get("profile_uuid")
            profile_type = ProfileService.get_profile_by_uuid(
                profile_uuid
            ).__class__.__name__
        citizenship_updated = (
            "citizenship" in validated_data
            and "PL" not in validated_data["citizenship"]
        )
        if spoken_languages := validated_data.pop(  # noqa: 5999
            "spoken_languages", None
        ):
            instance.spoken_languages.set([
                language.pk for language in spoken_languages
            ])
        instance = super().update(instance, validated_data)
        if profile_type == "PlayerProfile":
            if "birth_date" in validated_data or citizenship_updated:
                label_service.assign_youngster_label(profile_uuid)
        if profile_type == "CoachProfile":
            if "birth_date" in validated_data:
                label_service.assign_coach_age_labels(profile_uuid)

        return instance


class UserPreferencesUpdateSerializer(UserPreferencesSerializerDetailed):
    class Meta:
        model = UserPreferences
        exclude = (
            "user",
            "id",
        )


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
                context=self.context,
            )
            if user_preferences_serializer.is_valid(raise_exception=True):
                user_preferences_serializer.save()
        return super().update(instance, validated_data)


class MainUserDataSerializer(serializers.ModelSerializer):
    """Main user data serializer"""

    gender_display = serializers.SerializerMethodField()
    gender = serializers.CharField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "gender_display",
            "gender",
            "display_status",
        )

    def get_gender_display(self, obj: User) -> typing.Optional[dict]:
        """
        Retrieves and serializes the gender information from the user's preferences.

        This method accesses the gender attribute from the user's associated
        UserPreferences model. It then uses the ProfileEnumChoicesSerializer to
        serialize the gender value into a more readable format (e.g., converting
        a gender code to its corresponding descriptive name).
        """
        # Ensure the userpreferences relation exists
        if obj.userpreferences:
            gender_value = obj.userpreferences.gender
            if gender_value is not None:
                # Using ProfileEnumChoicesSerializer for the gender field
                serializer = ProfileEnumChoicesSerializer(
                    source="gender", model=UserPreferences
                )
                return serializer.to_representation(serializer.parse(gender_value))
            return None

    def update(self, instance: User, validated_data: dict) -> User:
        """Update User main data"""
        instance = super().update(instance, validated_data)

        # Custom handling for gender update
        gender_code = validated_data.get("gender", None)
        if gender_code is not None:
            instance.userpreferences.gender = gender_code
            instance.userpreferences.save()

        # display_status update
        instance.display_status = User.DisplayStatus.UNDER_REVIEW
        instance.save()

        return instance

    def validate_gender(self, value: str) -> str:
        """Validate gender field"""
        if value not in ["M", "K"]:
            raise InvalidGender
        return value


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


class PhoneNumberField(serializers.Field):
    """
    A custom field for handling phone numbers in the ManagerProfile serializer.

    This field is responsible for serializing and deserializing the phone number
    information (which includes 'dial_code' and 'agency_phone'). It handles the logic
    of combining these two separate fields into a single nested object for API
    representation, and it also processes incoming data for these fields
    in API requests.
    """

    def __init__(self, phone_field_name="phone_number", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.phone_field_name = (
            phone_field_name  # This can be 'phone_number' or 'agency_phone'
        )

    def run_validation(self, data=...):
        """Validate phone number field before creating object."""

        if data is not empty and not isinstance(data, dict):
            raise PhoneNumberMustBeADictionaryHTTPException
        return super().run_validation(data)

    def to_representation(self, obj: Any) -> Optional[typing.Dict[str, str]]:
        """
        Converts the object's phone number information into a nested
        JSON object for API output.
        """
        dial_code = getattr(obj, "dial_code", None)
        phone_number = getattr(obj, self.phone_field_name, None)

        if dial_code is None and phone_number is None:
            return None

        return {
            "dial_code": f"+{dial_code}" if dial_code is not None else None,
            "number": phone_number,
        }

    def to_internal_value(self, data: dict) -> dict:
        """
        Processes the incoming data for the phone number field.
        """
        internal_value = {}
        dial_code = data.get("dial_code")
        phone_number = (
            data.get("number")
            if self.phone_field_name == "phone_number"
            else data.get("agency_phone")
        )

        if dial_code is not None:
            internal_value["dial_code"] = dial_code
        if phone_number is not None:
            internal_value[self.phone_field_name] = phone_number

        return internal_value


class ProfileTransferStatusSerializer(
    serializers.ModelSerializer,
    SharedValidatorsMixin,
    PhoneNumberMixin,
    EmailUpdateMixin,
):
    """Transfer status serializer for user profile view"""

    class Meta:
        model = ProfileTransferStatus
        fields = (
            "contact_email",
            "phone_number",
            "status",
            "additional_info",
            "league",
            "benefits",
            "salary",
            "number_of_trainings",
        )

    contact_email = serializers.EmailField(required=False, allow_null=True)
    status = ProfileEnumChoicesSerializer(model=ProfileTransferStatus)
    additional_info = serializers.ListField(required=False, allow_null=True)
    league = serializers.PrimaryKeyRelatedField(
        queryset=LeagueService().get_leagues(), many=True
    )
    phone_number = PhoneNumberField(source="*", required=False)
    benefits = serializers.ListField(required=False, allow_null=True)

    def create(self, validated_data: dict):
        """Create transfer status"""
        profile = self.context.get("profile")
        transfer_status = ProfileService().get_profile_transfer_status(profile)
        if transfer_status:
            raise TransferStatusAlreadyExistsHTTPException

        validated_data: dict = TransferStatusService.prepare_generic_type_content(
            validated_data, profile
        )
        phone_number = validated_data.pop("phone_number", None)
        dial_code = validated_data.pop("dial_code", None)
        if phone_number or dial_code:
            self.update_phone_number(
                new_data={"phone_number": phone_number, "dial_code": dial_code},
                profile=profile,
                user_data_serializer=UserDataSerializer,
            )
        contact_email: Optional[str] = validated_data.pop("contact_email", None)
        if contact_email:
            self.update_email(
                new_email=contact_email,
                profile=profile,
                user_data_serializer=UserPreferencesSerializerDetailed,
            )
        return super().create(validated_data)

    def to_representation(self, instance: ProfileTransferStatus) -> dict:
        """
        Overrides to_representation method to return additional info
        as a list of strings.
        """
        data = super().to_representation(instance)
        data["league"] = LeagueSerializer(instance=instance.league, many=True).data
        if instance.additional_info:
            info = [
                ChoicesTuple(*transfer)
                for transfer in TRANSFER_STATUS_ADDITIONAL_INFO_CHOICES
                if transfer[0] in str(instance.additional_info)
            ]
            serializer = ProfileEnumChoicesSerializer(info, many=True)
            data["additional_info"] = serializer.data
        if instance.benefits:
            benefits = [
                ChoicesTuple(*transfer)
                for transfer in TRANSFER_BENEFITS_CHOICES
                if transfer[0] in str(instance.benefits)
            ]
            serializer = ProfileEnumChoicesSerializer(benefits, many=True)
            data["benefits"] = serializer.data
        if instance.salary:
            salary = [
                ChoicesTuple(*transfer)
                for transfer in TRANSFER_SALARY_CHOICES
                if transfer[0] in str(instance.salary)
            ]
            serializer = ProfileEnumChoicesSerializer(instance=salary[0])
            data["salary"] = serializer.data
        if instance.number_of_trainings:
            number_of_trainings = [
                ChoicesTuple(*transfer)
                for transfer in TRANSFER_TRAININGS_CHOICES
                if transfer[0] in str(instance.number_of_trainings)
            ]
            serializer = ProfileEnumChoicesSerializer(number_of_trainings, many=True)
            data["number_of_trainings"] = serializer.data
        user_preferences = instance.profile.user.userpreferences
        if user_preferences.phone_number:
            data["phone_number"] = PhoneNumberField(source="*").to_representation(
                user_preferences
            )
        if user_preferences.contact_email:
            data["contact_email"] = user_preferences.contact_email
        return data

    def to_internal_value(self, data):
        internal_value = super().to_internal_value(data)
        internal_value["additional_info"] = data.get("additional_info")
        return internal_value

    def update(self, instance: ProfileTransferStatus, validated_data: dict):
        """Update transfer status"""
        phone_number = validated_data.pop("phone_number", None)
        dial_code = validated_data.pop("dial_code", None)
        if phone_number or dial_code:
            self.update_partial_phone_number(
                new_data={"phone_number": phone_number, "dial_code": dial_code},
                instance=instance,
                user_data_serializer=UserDataSerializer,
            )
        contact_email: Optional[str] = validated_data.pop("contact_email", None)
        if contact_email:
            self.update_partial_email(
                new_email=contact_email,
                profile=self.context.get("profile"),
                user_data_serializer=UserPreferencesSerializerDetailed,
            )

        return super().update(instance, validated_data)


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


class ProfileTransferRequestSerializer(
    serializers.ModelSerializer,
    SharedValidatorsMixin,
    PhoneNumberMixin,
    EmailUpdateMixin,
):
    """Transfer request serializer for user profile view"""

    class Meta:
        model = ProfileTransferRequest
        fields = (
            "requesting_team",
            "gender",
            "status",
            "position",
            "number_of_trainings",
            "benefits",
            "salary",
            "contact_email",
            "phone_number",
            "profile_uuid",
            "club_voivodeship",
        )

    contact_email = serializers.EmailField(required=False, allow_null=True)
    club_voivodeship = serializers.CharField(source="voivodeship", read_only=True)
    profile_uuid = serializers.UUIDField(source="profile.uuid", read_only=True)
    requesting_team = serializers.PrimaryKeyRelatedField(
        queryset=TeamContributor.objects.all()
    )
    status = ProfileEnumChoicesSerializer(
        model=ProfileTransferRequest,
    )
    position = PlayerPositionSerializer(many=True, required=True)
    number_of_trainings = serializers.IntegerField(required=False, allow_null=True)
    benefits = serializers.ListField(required=False, allow_null=True)
    salary = serializers.IntegerField(required=False, allow_null=True)
    phone_number = PhoneNumberField(source="*", required=False)

    def to_representation(self, instance: ProfileTransferRequest) -> dict:
        """
        Overrides to_representation method to return additional info, position,
        number of trainings and salary as an objects represents
        by their names and ids.
        """
        serializer = ProfileEnumChoicesSerializer
        try:
            data = super().to_representation(instance)
        except AttributeError as exc:
            logger.error(f"Instance: {instance.__dict__} has wrong data", exc_info=True)
            raise AttributeError from exc

        data["requesting_team"] = TeamContributorSerializer(
            instance=instance.requesting_team, read_only=True, context=self.context
        ).data
        if instance.benefits:
            info = [
                ChoicesTuple(*transfer)
                for transfer in TRANSFER_BENEFITS_CHOICES
                if transfer[0] in str(instance.benefits)
            ]
            info_serialized = serializer(info, many=True)
            data["benefits"] = info_serialized.data
        if instance.position:
            positions = PlayerPositionSerializer(instance=instance.position, many=True)
            data["player_position"] = positions.data
        if instance.number_of_trainings:
            num_of_training_serialized = serializer(
                instance=instance.number_of_trainings,
                source="number_of_trainings",
                model=ProfileTransferRequest,
            )
            data["number_of_trainings"] = num_of_training_serialized.data
        if instance.salary:
            salary_serialized = serializer(
                instance=instance.salary,
                source="salary",
                model=ProfileTransferRequest,
            )
            data["salary"] = salary_serialized.data
        user_preferences = instance.profile.user.userpreferences
        if user_preferences.phone_number:
            data["phone_number"] = PhoneNumberField(source="*").to_representation(
                user_preferences
            )
        if user_preferences.contact_email:
            data["contact_email"] = user_preferences.contact_email
        return data

    def validate_requesting_team(
        self, requesting_team: TeamContributor
    ) -> TeamContributor:
        """Validate requesting team field"""
        owner = self.context.get("profile")
        if requesting_team.profile_uuid != owner.uuid:
            logger.error(
                f"Requesting team profile_uuid: {requesting_team.profile_uuid} "
                f"!= owner uuid: {owner.uuid}"
            )
            raise NotAOwnerOfTheTeamContributorHTTPException
        return requesting_team

    def create(self, validated_data: dict):
        """Create transfer request"""
        profile = self.context.get("profile")
        transfer_request = ProfileService().get_profile_transfer_request(profile)
        if transfer_request:
            raise TransferRequestAlreadyExistsHTTPException

        validated_data: dict = TransferStatusService.prepare_generic_type_content(
            validated_data, profile
        )
        phone_number = validated_data.pop("phone_number", None)
        dial_code = validated_data.pop("dial_code", None)
        if phone_number or dial_code:
            self.update_phone_number(
                new_data={"phone_number": phone_number, "dial_code": dial_code},
                profile=profile,
                user_data_serializer=UserDataSerializer,
            )
        contact_email: Optional[str] = validated_data.pop("contact_email", None)
        if contact_email:
            self.update_email(
                new_email=contact_email,
                profile=profile,
                user_data_serializer=UserPreferencesSerializerDetailed,
            )
        return super().create(validated_data)


class UpdateOrCreateProfileTransferSerializer(ProfileTransferRequestSerializer):
    position = PrimaryKeyRelatedField(queryset=PlayerPosition.objects.all(), many=True)

    def update(self, instance, validated_data):
        phone_number = validated_data.pop("phone_number", None)
        dial_code = validated_data.pop("dial_code", None)
        if phone_number or dial_code:
            self.update_partial_phone_number(
                new_data={"phone_number": phone_number, "dial_code": dial_code},
                instance=instance,
                user_data_serializer=UserDataSerializer,
            )
        contact_email: Optional[str] = validated_data.pop("contact_email", None)
        if contact_email:
            self.update_partial_email(
                new_email=contact_email,
                profile=self.context.get("profile"),
                user_data_serializer=UserPreferencesSerializerDetailed,
            )
        return super().update(instance, validated_data)


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
    data_fulfill_status = serializers.CharField(required=True)
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
            label_service.assign_goalkeeper_height_label(instance.uuid)

        return instance

    def get_transfer_status(self, obj: BaseProfile) -> Optional[dict]:
        """Get transfer status by player profile."""
        result: list = obj.transfer_status_related.first()
        if result:
            serializer = ProfileTransferStatusSerializer(result, required=False)
            return serializer.data
        return None

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
