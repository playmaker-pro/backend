from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, Optional, Type

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from profiles.interfaces import FulfillScoreProtocol
from roles.definitions import ProfileDataScore

if TYPE_CHECKING:
    from profiles.models import BaseProfile, ClubProfile, CoachProfile, PlayerProfile

User = get_user_model()


class VerificationObjectManager(models.Manager):
    def create_initial(self, owner: User):
        """Creates initial verifcation object for a profile based on current data."""
        if owner.is_club or owner.is_player or owner.coach() or owner.scout():
            defaults = owner.profile.get_verification_data_from_profile()
            defaults["set_by"] = User.get_system_user()
            defaults["previous"] = None
            return super().create(**defaults)


class PlayerProfileFulFillScore:
    """Calculate Player profile data scoring."""

    @staticmethod
    def data_fulfill_level(obj: "BaseProfile") -> ProfileDataScore:
        """
        Verify if the player profile data is fulfilled.

        The first acceptance criterion (level 1) is the verification stage (completed).
        The second acceptance criterion (level 2) includes fulfilled data in the following fields:
            - last_name
            - first_name
            - birth_date
            - player_positions
            - team_object

        Additionally, profile may achieve level 0 fulfillment if either of the following conditions are met:
        - The verification stage is completed, and either a profile picture or a pm_score value is populated.

        Returns:
            ProfileDataScore: The level of profile data fulfillment or None.
        """  # noqa: 501
        instance: "PlayerProfile" = obj  # noqa

        if (
            instance.verification_stage
            and instance.verification_stage.done is True
            and (
                bool(instance.user.picture)
                or (
                    hasattr(instance, "playermetrics")
                    and instance.playermetrics.pm_score is not None
                )
            )
        ):
            return ProfileDataScore.ZERO.value

        if instance.verification_stage and instance.verification_stage.done is True:
            return ProfileDataScore.ONE.value

        try:
            instance.user.userpreferences
        except ObjectDoesNotExist:
            return ProfileDataScore.THREE.value

        if (
            instance.user.last_name
            and instance.user.first_name
            and instance.user.userpreferences.birth_date
            and instance.player_positions.exists()
            and instance.team_object
        ):
            return ProfileDataScore.TWO.value
        return ProfileDataScore.THREE.value


class CoachProfileFulFillScore:
    """Calculate Coach profile data scoring."""

    @staticmethod
    def data_fulfill_level(obj: "BaseProfile") -> ProfileDataScore:
        """
        Verify if the coach profile data is fulfilled.

        The first acceptance criterion for the level 1 is the verification stage (completed).
        The second acceptance criterion (level 2) includes fulfilled data in the following fields:
            - last_name
            - first_name
            - birth_date
            - licences
            - team_object

        Additionally, profile may achieve level 0 fulfillment if the following condition is met:
        - The verification stage is completed, and a profile picture is populated.


        Returns:
            OProfileDataScore: The level of profile data fulfillment or None.
        """  # noqa: 501
        instance: "CoachProfile" = obj  # noqa
        if (
            instance.verification_stage
            and instance.verification_stage.done is True
            and instance.user.picture
        ):
            return ProfileDataScore.ZERO.value

        if instance.verification_stage and instance.verification_stage.done is True:
            return ProfileDataScore.ONE.value

        try:
            instance.user.userpreferences
        except ObjectDoesNotExist:
            return ProfileDataScore.THREE.value

        if (
            instance.user.last_name
            and instance.user.first_name
            and instance.user.userpreferences.birth_date
            and instance.user.licences.exists()
            and instance.team_object
        ):
            return ProfileDataScore.TWO.value
        return ProfileDataScore.THREE.value


class ClubProfileFulFillScore:
    """Calculate CLub profile data scoring."""

    @staticmethod
    def data_fulfill_level(obj: "BaseProfile") -> str:
        """
        Verify if the club profile data is fulfilled.

        The first acceptance criterion for level 1 is the verification stage.
        The second acceptance criterion (level 2) includes fulfilled data in the following fields:
            - last_name
            - first_name
            - birth_date
            - licences
            - team_object

        Additionally, profile may achieve level 0 fulfillment if the following condition is met:
        - The verification stage is completed, and a profile picture is populated.

        Returns:
            ProfileDataScore: The level of profile data fulfillment or None.
        """  # noqa: 501
        instance: "ClubProfile" = obj  # noqa
        if (
            instance.verification_stage
            and instance.verification_stage.done is True
            and instance.user.picture
        ):
            return ProfileDataScore.ZERO.value

        if instance.verification_stage and instance.verification_stage.done is True:
            return ProfileDataScore.ONE.value

        if (
            instance.user.last_name
            and instance.user.first_name
            and instance.club_role
            and instance.team_object
        ):
            return ProfileDataScore.TWO.value

        return ProfileDataScore.THREE.value


class OtherProfilesFulFillScore:
    """Calculate data scoring for other profiles."""

    @staticmethod
    def data_fulfill_level(obj) -> ProfileDataScore:
        """
        Verify if other profiles data is fulfilled.
        Acceptance criteria for level 1 is verification stage.
        There is no level 2.

        Additionally, profile may achieve level 0 fulfillment if the following condition is met:
        - The verification stage is completed, and a profile picture is populated.
        """  # noqa: 501
        if (
            obj.verification_stage
            and obj.verification_stage.done is True
            and obj.user.picture
        ):
            return ProfileDataScore.ZERO.value

        if obj.verification_stage and obj.verification_stage.done is True:
            return ProfileDataScore.ONE.value

        return ProfileDataScore.THREE.value


DATA_PROFILE_MAPPING = {
    "PlayerProfile": PlayerProfileFulFillScore,
    "CoachProfile": CoachProfileFulFillScore,
    "ClubProfile": ClubProfileFulFillScore,
    "ScoutProfile": OtherProfilesFulFillScore,
    "ManagerProfile": OtherProfilesFulFillScore,
    "GuestProfile": OtherProfilesFulFillScore,
}


def default_managers_mapping() -> Dict[str, Type[FulfillScoreProtocol]]:
    """Default mapping callable for managers default_factory in ProfileManager."""
    return DATA_PROFILE_MAPPING


@dataclass
class ProfileManager:
    """Base profile manager."""

    data_score_managers: Dict[str, Type[FulfillScoreProtocol]] = field(
        default_factory=default_managers_mapping
    )

    def get_data_score(self, obj: "BaseProfile") -> Optional[str]:
        """
        Returns level of profile data fulfillment
        or None if class name doesn't exist in mapper.
        """
        manager: Optional[FulfillScoreProtocol] = self.data_score_managers.get(
            type(obj).__name__
        )

        if manager:
            return manager.data_fulfill_level(obj)
        return None
