import typing
import uuid
from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from labels.models import Label, LabelDefinition
from labels.utils import (
    check_if_tall_goalkeeper,
    check_if_youngster,
    determine_licence_label,
    get_coach_age_label,
    get_label_end_date,
    get_licence_expiry_date,
)
from profiles.models import CoachProfile, PlayerProfile
from profiles.services import ProfileService
from users.models import UserPreferences

User = get_user_model()
profile_service = ProfileService()


class LabelService:
    """
    Service class for managing labels associated with user profiles.

    This service provides methods for retrieving, updating, and removing labels.
    Labels are used to categorize and provide specific information about user profiles,
    such as age categories, professional qualifications, and other criteria.
    """

    @staticmethod
    def get_label_definition(label_name: str) -> LabelDefinition:
        """
        Retrieves or creates a LabelDefinition object based on the provided parameters.
        """
        return LabelDefinition.objects.get(label_name=label_name)

    @staticmethod
    def update_label(
        user_id: int,
        label_def: LabelDefinition,
        end_date: typing.Optional[date],
        content_type: ContentType,
        visible_on_main_page: bool,
    ) -> None:
        """
        Updates an existing label instance for a given profile based on the
        existing label definition and end date.
        """
        # Attempt to update an existing label
        _, updated = Label.objects.update_or_create(
            content_type=content_type,
            object_id=user_id,
            label_definition=label_def,
            defaults={
                "visible": True,
                "visible_on_profile": True,
                "visible_on_base": True,
                "visible_on_main_page": visible_on_main_page,
                "end_date": end_date,
            },
        )
        if not updated:
            pass

    @staticmethod
    def remove_labels(
        user_id: int, label_names: list, content_type: ContentType
    ) -> None:
        """
        Removes specified labels from a given profile.
        """
        Label.objects.filter(
            content_type=content_type,
            object_id=user_id,
            label_definition__label_name__in=label_names,
        ).delete()

    def assign_youngster_label(self, profile_uuid: uuid.UUID) -> None:
        """
        Assigns or updates the 'Młodzieżowiec' label for a player profile.
        """
        player_profile = PlayerProfile.objects.get(uuid=profile_uuid)
        user_preferences: UserPreferences = UserPreferences.objects.get(
            user=player_profile.user
        )

        if not check_if_youngster(
            user_preferences.birth_date, user_preferences.citizenship
        ):
            self.remove_labels(
                player_profile.user.pk,
                [LabelDefinition.LabelNames.YOUTH],
                ContentType.objects.get_for_model(PlayerProfile),
            )
            return

        label_def: LabelDefinition = self.get_label_definition(
            LabelDefinition.LabelNames.YOUTH,
        )
        end_date = date(user_preferences.birth_date.year + 21, 6, 30)
        self.update_label(
            player_profile.user.pk,
            label_def,
            end_date,
            ContentType.objects.get_for_model(PlayerProfile),
            visible_on_main_page=True,
        )

    def assign_coach_age_labels(self, coach_profile_uuid: uuid.UUID) -> None:
        """
        Assigns or updates age-related labels for a coach profile.
        """
        coach_profile: CoachProfile = CoachProfile.objects.get(uuid=coach_profile_uuid)
        user_preferences: UserPreferences = UserPreferences.objects.get(
            user=coach_profile.user
        )

        birth_date = user_preferences.birth_date
        if birth_date is None:
            return

        self.remove_labels(
            coach_profile.user.pk,
            [
                LabelDefinition.LabelNames.COACH_AGE_30,
                LabelDefinition.LabelNames.COACH_AGE_40,
            ],
            ContentType.objects.get_for_model(CoachProfile),
        )

        today = date.today()
        age = (
            today.year
            - birth_date.year
            - ((today.month, today.day) < (birth_date.month, birth_date.day))
        )
        label_name: str = get_coach_age_label(age)

        if label_name:
            end_date = get_label_end_date(birth_date, age)
            label_def = self.get_label_definition(label_name)
            self.update_label(
                coach_profile.user.pk,
                label_def,
                end_date,
                ContentType.objects.get_for_model(CoachProfile),
                visible_on_main_page=False,
            )

    def assign_goalkeeper_height_label(self, player_profile_uuid: uuid.UUID) -> None:
        """
        Assigns or updates the 'HIGH_KEEPER' label for a player profile
        based on height criteria.

        This method checks if a player profile (identified by its UUID) meets the
        criteria for being labeled as a 'HIGH_KEEPER' (goalkeeper, height over 185 cm).
        If the criteria are met, the label is assigned or updated. If the criteria
        are no longer met, the label is removed.
        """
        player_profile = PlayerProfile.objects.get(uuid=player_profile_uuid)

        label_name = LabelDefinition.LabelNames.HIGH_KEEPER
        label_def = self.get_label_definition(label_name)

        # Determine if label should be present
        should_have_label = check_if_tall_goalkeeper(player_profile)

        if should_have_label:
            # Assign or update label
            self.update_label(
                player_profile.user.pk,
                label_def,
                None,  # No end date for this label
                ContentType.objects.get_for_model(PlayerProfile),
                visible_on_main_page=False,
            )
        else:
            # Remove label if it exists but criteria are no longer met
            self.remove_labels(
                player_profile.user.pk,
                [label_name],
                ContentType.objects.get_for_model(PlayerProfile),
            )

    def assign_licence_labels(self, user_id: int) -> None:
        """
        Assigns or updates UEFA license labels ('LICENCE_PRO', 'LICENCE_A')
        for a user based on their active licenses.

        The method also ensures the removal of
        labels if the corresponding licenses are no longer active or if
        the user doesn't have either of these licenses.
        """
        user = User.objects.get(pk=user_id)
        licence_label = determine_licence_label(user)
        if licence_label:
            label_def = self.get_label_definition(
                licence_label,
            )
            # Assign the label with the expiry date of the licence as the end date
            expiry_date = get_licence_expiry_date(user, licence_label)
            self.update_label(
                user_id,
                label_def,
                expiry_date,
                ContentType.objects.get_for_model(User),
                visible_on_main_page=True,
            )
            # Remove the opposite label if it exists
            opposite_label = (
                LabelDefinition.LabelNames.LICENCE_A
                if licence_label == LabelDefinition.LabelNames.LICENCE_PRO
                else LabelDefinition.LabelNames.LICENCE_PRO
            )
            self.remove_labels(
                user_id, [opposite_label], ContentType.objects.get_for_model(User)
            )
        else:
            # Remove both labels if they exist
            self.remove_labels(
                user_id,
                [
                    LabelDefinition.LabelNames.LICENCE_PRO,
                    LabelDefinition.LabelNames.LICENCE_A,
                ],
                ContentType.objects.get_for_model(User),
            )
