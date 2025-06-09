import logging
from functools import partial
from typing import Optional, Type, Union

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.consts import ChoicesTuple
from api.serializers import PhoneNumberField, ProfileEnumChoicesSerializer
from clubs.api.serializers import LeagueSerializer
from clubs.services import LeagueService
from profiles.api.errors import (
    NotAOwnerOfTheTeamContributorHTTPException,
    TransferRequestAlreadyExistsHTTPException,
    TransferStatusAlreadyExistsHTTPException,
)
from profiles.api.serializers import PlayerPositionSerializer
from profiles.models import BaseProfile, PlayerPosition, TeamContributor
from profiles.services import ProfileService, TransferStatusService
from roles.definitions import (
    TRANSFER_BENEFITS_CHOICES,
    TRANSFER_SALARY_CHOICES,
    TRANSFER_STATUS_ADDITIONAL_INFO_CHOICES,
    TRANSFER_TRAININGS_CHOICES,
)
from transfers.models import ProfileTransferRequest, ProfileTransferStatus
from users.api.serializers import UserDataSerializer, UserPreferencesSerializerDetailed

logger = logging.getLogger(__name__)


class EmailUpdateMixin:
    """Mixin for updating email for profile transfer request."""

    def partial_serializer(
        self,
        profile: BaseProfile,
        user_data_serializer: Type["UserPreferencesSerializerDetailed"],
        new_email: str,
    ) -> partial:
        """Create partial serializer for email update to avoid code duplication."""
        return partial(
            user_data_serializer,
            instance=profile.user.userpreferences,
            data={"contact_email": new_email},
            context=self.context,
        )

    def update_email(
        self,
        new_email: str,
        profile: BaseProfile,
        user_data_serializer: Type["UserPreferencesSerializerDetailed"],
    ) -> None:
        """Update email for profile transfer request."""
        user_serializer = self.partial_serializer(
            profile, user_data_serializer, new_email=new_email
        )()
        if user_serializer.is_valid(raise_exception=True):
            user_serializer.save()

    def update_partial_email(
        self,
        new_email: str,
        profile: BaseProfile,
        user_data_serializer: Type["UserPreferencesSerializerDetailed"],
    ) -> None:
        """Update email for profile transfer request. Partial case."""
        user_serializer = self.partial_serializer(
            profile, user_data_serializer, new_email=new_email
        )(partial=True)
        if user_serializer.is_valid(raise_exception=True):
            user_serializer.save()


class PhoneNumberMixin:
    """Mixin for updating phone number for profile transfer request."""

    def update_phone_number(
        self,
        new_data: dict,
        profile: BaseProfile,
        user_data_serializer: Type["UserDataSerializer"],
    ) -> None:
        """Update phone number for profile transfer request."""
        phone_number = new_data.get("phone_number")
        dial_code = new_data.get("dial_code")
        user_preferences = profile.user.userpreferences
        data = {"userpreferences": {}}
        if phone_number:
            data["userpreferences"]["phone_number"] = phone_number
        if dial_code:
            data["userpreferences"]["dial_code"] = dial_code

        user_serializer = partial(
            user_data_serializer,
            instance=profile.user,
            data=data,
            context=self.context,
        )

        if user_preferences.phone_number or user_preferences.dial_code:
            user = user_serializer(partial=True)
            if user.is_valid(raise_exception=True):
                user.save()
        else:
            user = user_serializer()
            if user.is_valid(raise_exception=True):
                user.save()

    def update_partial_phone_number(
        self,
        new_data: dict,
        instance: Union[
            "transfers.models.ProfileTransferStatus",
            "transfers.models.ProfileTransferRequest",
        ],
        user_data_serializer: Type["UserDataSerializer"],
    ) -> None:
        """Update phone number for profile transfer request. Partial case."""
        phone_number = new_data.get("phone_number")
        dial_code = new_data.get("dial_code")

        data_for_update = {}
        if phone_number:
            data_for_update["phone_number"] = phone_number
        if dial_code:
            data_for_update["dial_code"] = dial_code

        data = {"userpreferences": data_for_update}

        user_serializer = user_data_serializer(
            instance=instance.profile.user,
            data=data,
            context=self.context,
            partial=True,
        )

        if user_serializer.is_valid(raise_exception=True):
            user_serializer.save()


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
        from profiles.serializers_detailed.base_serializers import (
            TeamContributorSerializer,
        )

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
    position = serializers.PrimaryKeyRelatedField(
        queryset=PlayerPosition.objects.all(), many=True
    )

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
