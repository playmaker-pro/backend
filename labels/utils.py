import datetime
import typing
from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model, Q, QuerySet
from django.utils import timezone

from clubs.models import Season
from labels.models import Label, LabelDefinition
from profiles.models import PROFILE_TYPE, PlayerProfile

User = get_user_model()


def get_coach_age_label(age: int) -> str:
    """
    Determines the appropriate age label for a coach based on their age.
    """
    if age < 30:
        return LabelDefinition.LabelNames.COACH_AGE_30
    if 30 <= age < 40:
        return LabelDefinition.LabelNames.COACH_AGE_40
    return ""


def get_label_end_date(birth_date: datetime.date, age: int) -> datetime.date:
    """
    Calculates the end date for the coach's age label.
    """
    return birth_date + datetime.timedelta(days=365 * (30 if age < 30 else 40))


def check_if_youngster(birth_date: date, citizenship: list) -> bool:
    """
    Checks if a player is considered a "youngster" based on birth date and citizenship.
    """
    if birth_date is None or "PL" not in citizenship:
        return False
    return date(birth_date.year + 21, 6, 30) >= date.today()


def check_if_tall_goalkeeper(player_profile: PlayerProfile) -> bool:
    """
    Checks if a player profile belongs to a tall goalkeeper
    (height >= 185 cm and main position is goalkeeper).
    """
    is_goalkeeper = player_profile.player_positions.filter(
        player_position__id=9, is_main=True
    ).exists()
    meets_height_requirement = player_profile.height and player_profile.height >= 185
    return is_goalkeeper and meets_height_requirement


def determine_licence_label(user: User) -> str:
    """
    Determines the most relevant license label for a user based on their
    active licenses.

    This function checks if a user has any active UEFA PRO or UEFA A licenses.
    If the user has an active UEFA PRO license, it returns the label for UEFA PRO.
    If the user does not have an active UEFA PRO but has an active UEFA A license,
    it returns the label for UEFA A. Otherwise, it returns an empty string.
    """
    active_licences = user.licences.filter(
        Q(expiry_date__gte=date.today()) | Q(expiry_date__isnull=True)
    )
    if active_licences.filter(licence__name="UEFA PRO").exists():
        return LabelDefinition.LabelNames.LICENCE_PRO
    if active_licences.filter(licence__name="UEFA A").exists():
        return LabelDefinition.LabelNames.LICENCE_A
    return ""


def get_licence_expiry_date(user: User, licence_label: str) -> typing.Optional[date]:
    """
    Returns the expiry date of a specific licence for a user.
    """
    licence_name = licence_label.split()[-1]
    licence = user.licences.filter(licence__name=licence_name).first()
    return licence.expiry_date if licence else None


def fetch_all_labels(
    profile_object: PROFILE_TYPE, label_context: str
) -> typing.List[Label]:
    """
    Fetches all labels associated with a profile and its user, based on the specified context.
    """
    current_season = Season.objects.filter(is_current=True).first()
    today = timezone.now().date()

    # Common date filter
    date_filter = Q(
        Q(start_date__lte=today, end_date__gte=today)
        | Q(start_date__isnull=True, end_date__gte=today)
        | Q(end_date__isnull=True, start_date__lte=today)
        | Q(start_date__isnull=True, end_date__isnull=True)
    )

    # Adjust for the current season
    if current_season:
        season_filter = Q(season_name=current_season.name) | Q(season_name__isnull=True)
        date_filter &= season_filter
    else:
        date_filter &= Q(season_name__isnull=True)

    # Context-specific visibility filter
    visibility_filter = Q(visible=True)
    if label_context == "profile":
        visibility_filter &= Q(visible_on_profile=True)
    elif label_context == "base":
        visibility_filter &= Q(visible_on_base=True)

    # Apply the filters
    profile_labels = profile_object.labels.filter(date_filter & visibility_filter)
    user_labels = Label.objects.filter(
        date_filter & visibility_filter,
        content_type=ContentType.objects.get_for_model(User),
        object_id=profile_object.user_id,
    )

    return list(profile_labels) + list(user_labels)


def validate_labels(label_names: typing.List[str]) -> typing.List[str]:
    """
    Validates a list of label names against available label definitions.

    This function checks each label name in the provided list against the set of
    valid label names obtained from LabelDefinition. It returns a list containing
    only the label names that are valid.
    """
    valid_choices: typing.Set[str] = set(LabelDefinition.get_label_choices())
    return [label for label in label_names if label in valid_choices]


def get_profile_specific_ids(
    model, valid_label_names: typing.List[str]
) -> typing.Set[int]:
    """Get IDs for profiles with specific labels."""
    profile_content_type: ContentType = ContentType.objects.get_for_model(model)
    return Label.objects.filter(
        label_definition__label_name__in=valid_label_names,
        content_type=profile_content_type,
    ).values_list("object_id", flat=True)


def get_user_related_ids(valid_label_names: typing.List[str]) -> typing.Set[int]:
    """Get user IDs for user-related labels."""
    user_content_type: ContentType = ContentType.objects.get_for_model(User)
    return Label.objects.filter(
        label_definition__label_name__in=valid_label_names,
        content_type=user_content_type,
    ).values_list("object_id", flat=True)


def apply_label_filters(
    queryset: QuerySet,
    profile_specific_ids: typing.Set[int],
    user_related_ids: typing.Set[int],
    model: Model,
) -> QuerySet:
    """Apply the combined label filters to the queryset."""
    filtered_profile_ids: typing.Set = set(profile_specific_ids)
    if user_related_ids:
        profiles_of_users_ids = model.objects.filter(
            user__id__in=user_related_ids
        ).values_list("user_id", flat=True)
        filtered_profile_ids |= set(profiles_of_users_ids)

    return queryset.filter(pk__in=filtered_profile_ids)
