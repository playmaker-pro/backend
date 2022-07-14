import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from . import models


logger = logging.getLogger(__name__)


@receiver(post_save, sender=models.League)
def _post_save_league(sender, instance, created, **kwargs):
    # Identify and set highest parent

    if hasattr(instance, "_skip_post_save"):
        return

    if highest_parent := instance.get_highest_parent():
        instance.highest_parent = highest_parent
    try:
        instance._skip_post_save = True
        instance.save()
    finally:
        del instance._skip_post_save
