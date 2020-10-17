import logging

from django.conf import settings
from django.db.models.signals import pre_save
from django.dispatch import receiver

from . import models

logger = logging.getLogger("project")


@receiver(pre_save, sender=settings.AUTH_USER_MODEL)
def update_username_from_email(sender, instance, **kwargs):
    # This is mechanism to overwrite username for each account. s
    instance.username = instance.email
