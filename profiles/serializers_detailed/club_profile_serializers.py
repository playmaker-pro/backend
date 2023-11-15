from typing import Optional

from profiles.api.errors import InvalidClubRoleException, InvalidCustomClubRoleException
from profiles.api.serializers import ProfileEnumChoicesSerializer
from profiles.models import ClubProfile
from profiles.serializers_detailed.base_serializers import BaseProfileSerializer
from roles.definitions import CLUB_ROLES


class ClubProfileViewSerializer(BaseProfileSerializer):
    club_role = ProfileEnumChoicesSerializer(model=ClubProfile, required=False)

    class Meta:
        model = ClubProfile
        fields = (
            "slug",
            "user",
            "labels",
            "club_role",
            "custom_club_role",
            "profile_video",
            "external_links",
            "labels",
            "role",
            "verification_stage",
            "team_history_object",
        )


class ClubProfileUpdateSerializer(ClubProfileViewSerializer):
    """Serializer for updating club profile data."""

    def validate_club_role(self, club_role: Optional[str] = None) -> str:
        """
        Validates the club_role field to ensure it contains a valid choice.
        """
        expected_values = [role[0] for role in CLUB_ROLES]
        if club_role and club_role not in expected_values:
            raise InvalidClubRoleException(
                details=f"Club role is invalid. Expected one of: {expected_values}"
            )
        return club_role

    def update(self, instance: ClubProfile, validated_data: dict) -> ClubProfile:
        """Update club profile data. Overridden due to nested user data."""
        # Keep a reference to the old club_role before any update
        old_club_role = instance.club_role

        super().update(instance, validated_data)

        # Get the new club_role from validated_data or use the existing one if not provided
        new_club_role = validated_data.get("club_role", instance.club_role)
        # Check if custom_club_role is provided when club_role is not 'O'
        if "custom_club_role" in validated_data and new_club_role != "O":
            raise InvalidCustomClubRoleException()

        # Check if club_role is valid and update it
        if new_club_role and new_club_role != old_club_role:
            instance.club_role = new_club_role

        # Reset custom_club_role to None if club_role changes from 'O' to a different value
        if old_club_role == "O" and new_club_role != "O":
            instance.custom_club_role = None

        # Update custom_club_role if new club_role is 'Other' and custom_club_role is provided
        elif new_club_role == "O":
            if "custom_club_role" in validated_data:
                instance.custom_club_role = validated_data["custom_club_role"]

        return super().update(instance, validated_data)
