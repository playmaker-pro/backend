import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications.mail import mail_admins_about_new_user, mail_role_change_request
from roles import definitions

from . import models

logger = logging.getLogger(__name__)


def create_if_not_exist_user_account_settings(user):
    """
    Instance :  users.User
    """
    _, _ = models.NotificationSetting.objects.get_or_create(user=user)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_notification_settings_handler(sender, instance, created, **kwargs):
    """Signal reponsible for creating and attaching proper profile to user during creation process.

    Based on declared role append proper role (profile)
    """
    if (
        created
    ):  # this place is point where we decide if we want to update user's profile each time.
        logger.info(f"Attached account settings to user {instance}")
        create_if_not_exist_user_account_settings(instance)
