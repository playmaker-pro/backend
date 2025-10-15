from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from utils import GENDER_BASED_ROLES, OBJECTIVE_GENDER_BASED_ROLES


def build_email_context(
    user: settings.AUTH_USER_MODEL,
    user2: settings.AUTH_USER_MODEL = None,
    **kwargs,
) -> dict:
    """Builds a dictionary with context for email templates."""
    base_context = {
        "user": user,
        "user2": user2,
        "current_year": timezone.now().year,
        **kwargs,
    }
    context = kwargs.pop("context", {})
    if (
        kwargs.get("mailing_type") is not None
        and user.mailing
        and user.mailing.preferences
    ):
        context["unsubscribe_link"] = build_unsubscribe_link(
            user, kwargs["mailing_type"]
        )

    base_context.update(context)
    related_context = _get_gendered_context(user2) if user2 else {}
    base_context.update({
        "recipient_full_name": user.display_full_name,
        "related_full_name": user2.display_full_name if user2 else None,
        "related_user": user2,
        **related_context,
    })
    return base_context


def _get_gendered_context(user: settings.AUTH_USER_MODEL) -> dict:
    """Builds a dictionary with gender-aware fields used in email templates or messages."""
    if not user.declared_role or not user.userpreferences.gender:
        return {
            "related_role": _("Użytkownik"),
            "related_role_biernik": _("użytkownika"),
        }

    gender_index = int(user.userpreferences.gender == "K")

    return {
        "related_role": _(GENDER_BASED_ROLES[user.declared_role][gender_index]),
        "related_role_biernik": _(
            OBJECTIVE_GENDER_BASED_ROLES[user.declared_role][gender_index]
        ),
    }


def build_unsubscribe_link(user: settings.AUTH_USER_MODEL, mailing_type: str) -> str:
    """Builds a full unsubscribe link for the user with the given token."""
    return settings.BASE_URL + reverse(
        "api:mailing:update_preferences_directly",
        kwargs={
            "preferences_uuid": user.mailing.preferences.uuid,
            "mailing_type": mailing_type,
        },
    )
