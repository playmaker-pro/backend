from typing import List, Optional

from rest_framework import serializers

from profiles.api.errors import (
    InvalidCoachRoleException,
    InvalidFormationException,
    InvalidCustomCoachRoleException,
)
from profiles.api.serializers import ProfileEnumChoicesSerializer
from profiles.models import FORMATION_CHOICES, CoachProfile, ProfileVideo
from profiles.serializers_detailed.base_serializers import BaseProfileSerializer


class ProfileVideoSerializer(serializers.ModelSerializer):
    thumbnail = serializers.CharField(
        source="get_youtube_thumbnail_url", read_only=True
    )
    label = ProfileEnumChoicesSerializer(model=ProfileVideo, required=False)

    class Meta:
        model = ProfileVideo
        fields = (
            "id",
            "url",
            "title",
            "description",
            "label",
            "thumbnail",
        )


class CoachProfileViewSerializer(BaseProfileSerializer):
    """Serializer for retrieving coach profile data."""

    formation = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = CoachProfile
        fields = (
            "slug",
            "user",
            "external_links",
            "coach_role",
            "custom_coach_role",
            "training_ready",
            "formation",
            "profile_video",
            "labels",
            "role",
            "verification_stage",
            "team_history_object",
        )

    coach_role = ProfileEnumChoicesSerializer(model=CoachProfile, required=False)
    training_ready = ProfileEnumChoicesSerializer(
        required=False,
        model=CoachProfile,
    )


class CoachProfileUpdateSerializer(CoachProfileViewSerializer):
    """Serializer for updating coach profile data."""

    def validate_formation(self, formation: Optional[str] = None) -> str:
        expected_values: List[str] = [el[0] for el in FORMATION_CHOICES]
        if formation and formation not in expected_values:
            raise InvalidFormationException(
                details=f"Given formation is invalid. Expected one of: {expected_values}"
            )
        return formation

    def update(self, instance: CoachProfile, validated_data: dict) -> CoachProfile:
        """Update coach profile data. Overridden due to nested user data."""
        super().update(instance, validated_data)

        if coach_role := validated_data.get("coach_role"):  # noqa: E999
            if coach_role not in [role[0] for role in CoachProfile.COACH_ROLE_CHOICES]:
                expected_values: List[str] = [
                    el[0] for el in CoachProfile.COACH_ROLE_CHOICES
                ]
                raise InvalidCoachRoleException(
                    details=f"Coach role is invalid. Expected values: {expected_values}"
                )
            instance.coach_role = coach_role

        # Additional logic for handling 'custom_coach_role'
        # If 'coach_role' is not provided, use the existing one from the instance
        coach_role = validated_data.get("coach_role", instance.coach_role)

        # If 'coach_role' is "OTC", check for 'custom_coach_role'. If not, ensure 'custom_coach_role' is not provided.
        if coach_role == "OTC":
            custom_coach_role = validated_data.get("custom_coach_role", None)
            instance.custom_coach_role = custom_coach_role
        else:
            if (
                "custom_coach_role" in validated_data
                and validated_data.get("custom_coach_role") is not None
            ):
                raise InvalidCustomCoachRoleException()
            # Reset custom_coach_role to None if coach_role is not "OTC"
            instance.custom_coach_role = None

        if formation := validated_data.get("formation"):
            instance.formation = formation

        return super().update(instance, validated_data)
