from typing import List, Optional

from rest_framework import serializers

from profiles.api.errors import (
    InvalidCoachRoleException,
    InvalidCustomCoachRoleException,
    InvalidFormationException,
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
            "uuid",
            "user",
            "external_links",
            "coach_role",
            "custom_coach_role",
            "training_ready",
            "formation",
            "transfer_status",
            "profile_video",
            "labels",
            "role",
            "verification_stage",
            "team_history_object",
            "visits",
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
                details=f"Given formation is invalid. "
                f"Expected one of: {expected_values}"
            )
        return formation

    def validate_coach_role(self, coach_role: Optional[str] = None) -> str:
        """
        Validates the coach_role field to ensure it contains a valid choice.
        """
        expected_values = [role[0] for role in CoachProfile.COACH_ROLE_CHOICES]
        if coach_role and coach_role not in expected_values:
            raise InvalidCoachRoleException(
                details=f"Coach role is invalid. Expected one of: {expected_values}"
            )
        return coach_role

    def update(self, instance: CoachProfile, validated_data: dict) -> CoachProfile:
        """Update coach profile data. Overridden due to nested user data."""
        # Keep a reference to the old coach_role before any update
        old_coach_role = instance.coach_role

        super().update(instance, validated_data)

        # Retrieve the new coach_role from validated_data,
        # default to existing role if not provided
        new_coach_role = validated_data.get("coach_role", instance.coach_role)

        # Raise an exception if custom_coach_role is provided but the
        # new coach_role is not 'Other'
        if "custom_coach_role" in validated_data and new_coach_role != "OTC":
            raise InvalidCustomCoachRoleException()

        # Update the coach_role on the instance if it has changed
        if new_coach_role and new_coach_role != old_coach_role:
            instance.coach_role = new_coach_role

        # Reset custom_coach_role to None if coach_role changes from
        # 'Other' to a different role
        if old_coach_role == "OTC" and new_coach_role != "OTC":
            instance.custom_coach_role = None

        # Update custom_coach_role if new coach_role is 'Other' and
        # custom_coach_role is provided
        elif new_coach_role == "OTC":
            if "custom_coach_role" in validated_data:
                instance.custom_coach_role = validated_data["custom_coach_role"]

        if formation := validated_data.get("formation"):  # noqa: E999
            instance.formation = formation

        return super().update(instance, validated_data)
