from django.utils.translation import gettext_lazy as _
from inquiries.utils import GENDER_BASED_ROLES, OBJECTIVE_GENDER_BASED_ROLES

def build_email_context(user, log=None, context=None, **kwargs) -> dict:
    """Builds a dictionary with context for email templates."""
    base_context = {
        "user": user,
        **kwargs
    }

    if context:
        base_context.update(context)

    if log:
        base_context.update({
            "log": log,
            "recipient_full_name": log.log_owner.user.display_full_name,
            "related_full_name": log.related_with.user.display_full_name,
            "related_user": log.related_with.user,
            **_get_gendered_context(log),
        })
    return base_context

def _get_gendered_context(log) -> dict:
    """Builds a dictionary with gender-aware fields used in email templates or messages."""
    if not log:
        return {}
        
    related_user = log.related_with.user

    gender_index = int(related_user.userpreferences.gender == "K")
    return {
        "related_role": _(GENDER_BASED_ROLES[related_user.declared_role][gender_index]),
        "related_role_biernik": _(OBJECTIVE_GENDER_BASED_ROLES[related_user.declared_role][gender_index]),
    }
