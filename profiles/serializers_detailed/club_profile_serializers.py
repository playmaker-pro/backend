from typing import List

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

        # Additional logic for handling 'custom_club_role'
        # If 'club_role' is not provided, use the existing one from the instance
        club_role = validated_data.get("club_role", instance.club_role)

        # If 'club_role' is "O", check for 'custom_club_role'. If not, ensure 'custom_club_role' is not provided.
        if club_role == "O":
            custom_club_role = validated_data.get("custom_club_role", None)
            instance.custom_club_role = custom_club_role
        else:
            if (
                "custom_club_role" in validated_data
                and validated_data.get("custom_club_role") is not None
            ):
                raise InvalidCustomClubRoleException()
            # Reset custom_club_role to None if club_role is not "O"
            instance.custom_club_role = None

        return super().update(instance, validated_data)
