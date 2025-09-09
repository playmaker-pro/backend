import typing

from django.utils.translation import gettext as _
from rest_framework import serializers

from api.serializers import PhoneNumberField, ProfileEnumChoicesSerializer
from clubs.api.serializers import TeamHistoryBaseProfileSerializer
from inquiries import models as _models
from profiles.api.serializers import (
    PlayerProfilePositionSerializer as _PlayerProfilePositionSerializer,
)
from profiles.serializers_detailed.player_profile_serializers import (
    PlayerMetricsSerializer,
)
from users.api.serializers import BaseUserDataSerializer as _BaseUserDataSerializer
from users.models import User, UserPreferences


class InquiryContactSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.contact_email", allow_null=True)
    phone_number = PhoneNumberField(source="*", required=False)

    class Meta:
        model = UserPreferences
        fields = (
            "phone_number",
            "email",
        )


class InquiryUserDataSerializer(_BaseUserDataSerializer):
    age = serializers.IntegerField(read_only=True, source="userpreferences.age")
    specific_role = serializers.SerializerMethodField()
    custom_role = serializers.CharField(
        source="profile.profile_based_custom_role", read_only=True
    )
    uuid = serializers.UUIDField(source="profile.uuid", read_only=True)
    slug = serializers.CharField(source="profile.slug", read_only=True)
    player_position = _PlayerProfilePositionSerializer(
        source="profile.get_main_position", read_only=True
    )
    team_history_object = serializers.SerializerMethodField()
    gender = serializers.SerializerMethodField("get_gender")
    contact = InquiryContactSerializer(source="userpreferences", read_only=True)
    playermetrics = PlayerMetricsSerializer(
        read_only=True, source="profile.playermetrics"
    )

    def get_specific_role(self, obj: User) -> typing.Optional[dict]:
        """Get specific role for profile (Coach, Club)"""
        if obj.profile:
            if field_name := obj.profile.specific_role_field_name:
                val = getattr(obj.profile, field_name, None)
                if val is None:
                    return None
                serializer = ProfileEnumChoicesSerializer(
                    source=field_name,
                    read_only=True,
                    model=obj.profile.__class__,
                )
                return serializer.to_representation(serializer.parse(val))

    def get_team_history_object(self, obj: User) -> typing.Optional[dict]:
        """
        Custom method to handle team history serialization.
        Checks if the user has a profile with a team_object and serializes it.
        """
        profile = getattr(obj, "profile", None)
        if profile and hasattr(profile, "team_object"):
            return TeamHistoryBaseProfileSerializer(profile.team_object).data
        return None

    def get_gender(self, obj: User) -> typing.Optional[dict]:
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

    class Meta(_BaseUserDataSerializer.Meta):
        fields = _BaseUserDataSerializer.Meta.fields + (
            "age",
            "custom_role",
            "uuid",
            "slug",
            "player_position",
            "specific_role",
            "team_history_object",
            "gender",
            "contact",
            "playermetrics",
        )


class InquiryRequestSerializer(serializers.ModelSerializer):
    sender_object = InquiryUserDataSerializer(read_only=True, source="sender")
    recipient_object = InquiryUserDataSerializer(
        read_only=True, source="recipient", required=False
    )

    class Meta:
        model = _models.InquiryRequest
        fields = "__all__"

    def get_translated_status(self, status: str) -> str:
        """Translate inquiry status to current language."""
        status_translations = {
            _models.InquiryRequest.STATUS_NEW: _("NOWE"),
            _models.InquiryRequest.STATUS_SENT: _("WYSŁANO"),
            _models.InquiryRequest.STATUS_RECEIVED: _("PRZECZYTANE"),
            _models.InquiryRequest.STATUS_ACCEPTED: _("ZAAKCEPTOWANE"),
            _models.InquiryRequest.STATUS_REJECTED: _("ODRZUCONE"),
        }
        return status_translations.get(status, status)

    def to_representation(self, instance: _models.InquiryRequest) -> None:
        """Custom representation for InquiryRequest, handling recipient data and status translation."""
        data = super().to_representation(instance)
        # Translate status
        data["status"] = self.get_translated_status(instance.status)

        # Handle anonymous recipient by using stored UUID for security
        if (
            instance.anonymous_recipient
            and instance.status != _models.InquiryRequest.STATUS_ACCEPTED
        ):
            recipient = data.get("recipient_object", {})
            
            # Use stored anonymous UUID for secure historical preservation
            anonymous_uuid = None
            if instance.recipient_anonymous_uuid:
                # Use stored UUID (preferred - historical preservation)
                anonymous_uuid = str(instance.recipient_anonymous_uuid)
            else:
                # Fallback to current transfer object UUID (for existing data)
                if hasattr(instance.recipient, 'profile') and hasattr(instance.recipient.profile, 'meta'):
                    transfer_object = instance.recipient.profile.meta.transfer_object
                    if transfer_object and transfer_object.is_anonymous:
                        anonymous_uuid = str(transfer_object.anonymous_uuid)
            
            # Set secure anonymous slug and UUID
            if anonymous_uuid:
                recipient["slug"] = f"anonymous-{anonymous_uuid}"
                recipient["uuid"] = anonymous_uuid
            else:
                # Last resort fallback (should not happen with proper data)
                recipient["slug"] = "anonymous-unknown"
                recipient["uuid"] = "unknown"
            
            # Anonymize other recipient data
            recipient["id"] = 0
            recipient["first_name"] = "Anonimowy"
            recipient["last_name"] = "profil"
            recipient["picture"] = None
            recipient["team_history_object"] = None
            recipient["contact"] = {
                "email": None,
                "phone_number": {"dial_code": None, "number": None},
            }
            data["recipient_object"] = recipient

        return data

    def validate(self, attrs: dict) -> dict:
        """Validate if user can make request"""
        if not self.instance:
            sender: User = attrs.get("sender")
            recipient: User = attrs.get("recipient")
            userinquiry: _models.UserInquiry = sender.userinquiry

            if not userinquiry.can_make_request:
                raise serializers.ValidationError(
                    f"You have reached your limit of inquiries "
                    f"({userinquiry.counter}/{userinquiry.limit})."
                )

            if _models.InquiryRequest.objects.filter(
                sender=sender,
                recipient=recipient,
                anonymous_recipient=attrs.get("anonymous_recipient", False),
            ).first():
                raise serializers.ValidationError(
                    f"You have already sent inquiry to {recipient}."
                )

            if cross_request := _models.InquiryRequest.objects.filter(
                sender=recipient, recipient=sender
            ).first():
                if cross_request.status == _models.InquiryRequest.STATUS_ACCEPTED:
                    raise serializers.ValidationError(
                        "This user has already accepted your request."
                    )
                if cross_request.status != _models.InquiryRequest.STATUS_REJECTED:
                    self._accept_cross_request(cross_request)

        return attrs

    def _accept_cross_request(
        self, cross_request: _models.InquiryRequest
    ) -> "InquiryRequestSerializer":
        """
        Cross request is case when user A send request to user B
        when user B already sent request to user A.
        We want to auto-accept this kind of request and avoid creating new one.
        """
        return InquiryRequestSerializer(cross_request).accept()

    def accept(self) -> "InquiryRequestSerializer":
        """Accept inquiry request"""
        self.instance.accept()
        self.instance.save()
        return self

    def reject(self) -> "InquiryRequestSerializer":
        """Reject inquiry request"""
        self.instance.reject()
        self.instance.save()
        return self

    def create(
        self, validated_data: typing.Dict[str, typing.Any]
    ) -> _models.InquiryRequest:
        """
        Overrides the default create method to handle the creation of an InquiryRequest.

        This method extracts the recipient_profile_uuid from the validated data if
        present, then creates an InquiryRequest instance with the remaining
        validated data. The recipient_profile_uuid is used to perform additional
        logic specific to the InquiryRequest during its creation.
        """
        recipient_profile_uuid = validated_data.pop("recipient_profile_uuid", None)
        
        # If this is an anonymous inquiry, store the UUID for historical preservation
        if validated_data.get("anonymous_recipient") and recipient_profile_uuid:
            validated_data["recipient_anonymous_uuid"] = recipient_profile_uuid
        
        inquiry_request = _models.InquiryRequest(**validated_data)
        inquiry_request.is_read_by_sender = True
        inquiry_request.is_read_by_recipient = False
        inquiry_request.save()
        return inquiry_request


class InquiryPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = _models.InquiryPlan
        exclude = ("sort",)

    def to_representation(self, instance: _models.InquiryPlan) -> dict:
        """Override to provide dynamic translation of plan fields."""
        data = super().to_representation(instance)

        # Translate plan name and description dynamically
        # These are stored in the database and need runtime translation
        if instance.name:
            data["name"] = _(instance.name)

        if instance.description:
            data["description"] = _(instance.description)

        return data


class UserInquiryLogSerializer(serializers.ModelSerializer):
    message_type = serializers.CharField(source="message.log_type", read_only=True)
    body = serializers.SerializerMethodField(
        method_name="get_log_message", read_only=True
    )

    class Meta:
        model = _models.UserInquiryLog
        fields = ("created_at", "message_type", "body")

    def get_log_message(self, obj: _models.UserInquiryLog) -> str:
        """Get message body with user related data"""
        return obj.log_message_body


class InquiryPoolDetailsSerializer(serializers.Serializer):
    used = serializers.IntegerField()
    total = serializers.IntegerField()

    def to_representation(self, data):
        if isinstance(data, tuple):
            return {
                "used": data[0],
                "total": data[1],
            }
        return super().to_representation(data)


class InquiryPoolSerializer(serializers.Serializer):
    premium_profile = InquiryPoolDetailsSerializer(source="premium_profile_pool")
    regular = InquiryPoolDetailsSerializer(source="regular_pool")


class UserInquirySerializer(serializers.ModelSerializer):
    plan = InquiryPlanSerializer(read_only=True)
    contact = InquiryContactSerializer(source="user.userpreferences", read_only=True)
    inquiries_left = serializers.IntegerField(source="left_to_show")
    days_until_expiry = serializers.IntegerField(
        read_only=True, source="get_days_until_next_reference"
    )
    # logs = UserInquiryLogSerializer(many=True, read_only=True)
    unlimited = serializers.BooleanField(
        read_only=True, source="has_unlimited_inquiries"
    )
    limit = serializers.IntegerField(read_only=True, source="limit_to_show")
    counter = serializers.IntegerField(read_only=True)
    pools = InquiryPoolSerializer(source="*", read_only=True)

    class Meta:
        model = _models.UserInquiry
        exclude = ("counter_raw", "limit_raw")
