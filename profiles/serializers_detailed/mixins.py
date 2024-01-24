from functools import partial
from typing import TYPE_CHECKING, Type, Union

from profiles.models import BaseProfile, ProfileTransferRequest, ProfileTransferStatus

if TYPE_CHECKING:
    from profiles.serializers_detailed.base_serializers import (
        UserDataSerializer,
        UserPreferencesSerializerDetailed,
    )


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
        instance: Union["ProfileTransferStatus", "ProfileTransferRequest"],
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
