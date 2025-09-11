from django.db.models.signals import post_save
from django.dispatch import receiver

from external_links import models
from profiles.services import NotificationService


@receiver(post_save, sender=models.ExternalLinksEntity)
def post_external_link_create(sender, instance, created, **kwargs):
    """
    Signal to handle the creation of external links.
    """
    if created:
        if (
            instance.target.links.count() == 1
            and instance.target.owner.__class__.__name__.endswith("Profile")
        ):
            if meta := instance.target.owner.meta:
                NotificationService(meta).notify_profile_verified()
