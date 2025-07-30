from django.db.models.signals import post_save
from django.dispatch import receiver

from premium import models
from profiles.tasks import premium_expired


@receiver(post_save, sender=models.PremiumProfile)
def post_save_premium_profile(sender, instance, created, **kwargs):
    """
    Signal to handle actions after a premium profile is saved.
    """
    if not created:
        old_object = models.PremiumProfile.objects.get(pk=instance.pk)

        if old_object.valid_until is not None and instance.valid_until is None:
            premium_expired.delay(instance.premium_products.pk)
