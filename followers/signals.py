from django.db.models.signals import post_save
from django.dispatch import receiver

from followers import models
from notifications.services import NotificationService


@receiver(post_save, sender=models.Follow)
def post_follow(sender, instance, created, **kwargs) -> None:
    if created:
        NotificationService(instance.target.profile.meta).notify_new_follower()
