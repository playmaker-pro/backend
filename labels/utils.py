import typing

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model, QuerySet

from labels.models import Label, LabelDefinition

User = get_user_model()


def validate_labels(label_names: typing.List[str]) -> typing.List[str]:
    """
    Validates a list of label names against available label definitions.

    This function checks each label name in the provided list against the set of
    valid label names obtained from LabelDefinition. It returns a list containing
    only the label names that are valid.
    """
    valid_choices: typing.Set[str] = set(LabelDefinition.get_label_choices())
    return [label for label in label_names if label in valid_choices]


def get_profile_specific_ids(model, valid_label_names: typing.List[str]) -> typing.Set[int]:
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
