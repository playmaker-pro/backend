from django.db.models.signals import post_save
from django.dispatch import receiver

from followers import models
from notifications.services import NotificationService


@receiver(post_save, sender=models.GenericFollow)
def post_follow(sender, instance, created, **kwargs) -> None:
    if created:
        instance.user.profile.refresh_from_db()
        NotificationService(instance.user.profile.meta).notify_new_follower()
