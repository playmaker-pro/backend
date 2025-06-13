from django.db.models.signals import post_save
from django.dispatch import receiver

from followers import models
from notifications.services import NotificationService


@receiver(post_save, sender=models.GenericFollow)
def post_follow(sender, instance, created, **kwargs) -> None:
    if created:
        if instance.content_type.model.endswith("profile"):
            NotificationService(instance.content_object.meta).notify_new_follower()
