from celery import shared_task
from django.contrib.auth import get_user_model

from users.models import Ref, UserPreferences
from users.services import UserService

User = get_user_model()


@shared_task
def prepare_new_user(*args, **kwargs) -> None:
    """
    Create required/related objects for new user.
    """
    user = User.objects.get(pk=kwargs.get("user_id"))

    if not hasattr(user, "userpreferences"):
        UserPreferences.objects.get_or_create(user=user)

    if not hasattr(user, "ref"):
        Ref.objects.get_or_create(user=user)


@shared_task
def send_email_to_confirm_new_user(*args, **kwargs) -> None:
    """
    Send an email to new user to confirm his account.
    """
    user = User.objects.get(pk=kwargs.get("user_id"))
    UserService.send_email_to_confirm_new_user(user)
