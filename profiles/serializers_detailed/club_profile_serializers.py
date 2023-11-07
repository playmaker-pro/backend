from typing import List
from rest_framework import serializers

from profiles.api.errors import InvalidClubRoleException, InvalidCustomClubRoleException
from profiles.models import ClubProfile
from profiles.serializers_detailed.base_serializers import BaseProfileSerializer
from roles.definitions import CLUB_ROLES


class ClubProfileViewSerializer(BaseProfileSerializer):
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
    """Serializer for updating coach profile data."""

    def update(self, instance: ClubProfile, validated_data: dict) -> ClubProfile:
        """Update club profile data. Overridden due to nested user data."""
        super().update(instance, validated_data)

        # Handle club_role
        if club_role := validated_data.get("club_role"):
            # Ensure club_role is valid
            if club_role not in [role[0] for role in CLUB_ROLES]:
                expected_values: List[str] = [el[0] for el in CLUB_ROLES]
                raise InvalidClubRoleException(
                    details=f"Club role is invalid. Expected values: {expected_values}"
                )
            instance.club_role = club_role

            # Handle custom_club_role
            if club_role == "O":  # 'O' corresponds to 'Other' or 'Inne'
                custom_club_role = validated_data.get("custom_club_role")
                instance.custom_club_role = custom_club_role
            else:
                # If club_role is not 'Other' (Inne), then reset custom_club_role to None.
                instance.custom_club_role = None
                # If custom_club_role is present in validated_data, raise an error.
                if validated_data.get("custom_club_role"):
                    raise InvalidCustomClubRoleException()

        return super().update(instance, validated_data)
