import logging

from celery import chain
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from users.tasks import prepare_new_user, send_email_to_confirm_new_user

logger = logging.getLogger("project")
User = get_user_model()


@receiver(pre_save, sender=User)
def pre_save_user(sender, instance, **kwargs):
    # This is mechanism to overwrite username for each account. s
    instance.username = instance.email


@receiver(post_save, sender=User)
def post_create_user(sender, instance, created, **kwargs) -> None:
    """Create UserPreferences object for each new user"""
    if created:
        chain(
            prepare_new_user.s(user_id=instance.pk),
            send_email_to_confirm_new_user.s(user_id=instance.pk),
        ).apply_async()
