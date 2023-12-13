import typing

from rest_framework import serializers

from profiles.models import ManagerProfile
from profiles.serializers_detailed.base_serializers import BaseProfileSerializer


class PhoneNumberField(serializers.Field):
    """
    A custom field for handling phone numbers in the ManagerProfile serializer.

    This field is responsible for serializing and deserializing the phone number
    information (which includes 'dial_code' and 'agency_phone'). It handles the logic
    of combining these two separate fields into a single nested object for API
    representation, and it also processes incoming data for these fields in
    API requests.
    """

    def to_representation(
        self, obj: ManagerProfile
    ) -> typing.Optional[typing.Dict[str, str]]:
        """
        Converts the ManagerProfile instance's phone number information into
        a nested JSON object suitable for API output.
        """
        if obj.dial_code is None and obj.agency_phone is None:
            return None
        return {"dial_code": obj.dial_code, "agency_phone": obj.agency_phone}

    def to_internal_value(
        self, data: typing.Dict[str, typing.Any]
    ) -> typing.Dict[str, typing.Any]:
        """
        Processes the incoming data for the phone number field.

        This method is responsible for parsing and validating the 'dial_code' and
        'agency_phone' from the incoming nested object. It ensures that partial updates
        are correctly handled by not overriding existing values with None when
        not provided.
        """
        internal_value = {}
        if "dial_code" in data:
            internal_value["dial_code"] = data["dial_code"]
        if "agency_phone" in data:
            internal_value["agency_phone"] = data["agency_phone"]
        return internal_value


class ManagerProfileViewSerializer(BaseProfileSerializer):
    phone_number = PhoneNumberField(source="*")

    class Meta:
        model = ManagerProfile
        fields = (
            "slug",
            "uuid",
            "user",
            "labels",
            "profile_video",
            "external_links",
            "labels",
            "role",
            "verification_stage",
            "phone_number",
            "agency_email",
            "agency_transfermarkt_url",
            "agency_website_url",
            "agency_instagram_url",
            "agency_twitter_url",
            "agency_facebook_url",
            "agency_other_url",
            "team_history_object",
        )


class ManagerProfileUpdateSerializer(ManagerProfileViewSerializer):
    """Serializer for updating manager profile data."""

    phone_number = PhoneNumberField(required=False, source="*")

    class Meta(ManagerProfileViewSerializer.Meta):
        model = ManagerProfile
        fields = ManagerProfileViewSerializer.Meta.fields + ("phone_number",)

    def update(self, instance: ManagerProfile, validated_data: dict) -> ManagerProfile:
        """
        Updates the ManagerProfile instance with the given validated data.

        This method updates the phone number of the ManagerProfile instance based on
        the provided validated data within the nested 'phone_number' object.
        """
        phone_data = validated_data.pop("phone_number", None)
        if phone_data:
            instance.dial_code = phone_data.get("dial_code", instance.dial_code)
            instance.agency_phone = phone_data.get(
                "agency_phone", instance.agency_phone
            )

        return super().update(instance, validated_data)
