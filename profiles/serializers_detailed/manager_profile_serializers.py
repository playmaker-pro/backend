from profiles.models import ManagerProfile
from profiles.serializers_detailed.base_serializers import (
    BaseProfileSerializer,
    PhoneNumberField,
)


class ManagerProfileViewSerializer(BaseProfileSerializer):
    phone_number = PhoneNumberField(source="*", phone_field_name="agency_phone")

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
            "visits",
        )


class ManagerProfileUpdateSerializer(ManagerProfileViewSerializer):
    """Serializer for updating manager profile data."""

    phone_number = PhoneNumberField(
        required=False, phone_field_name="agency_phone", source="*"
    )

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
