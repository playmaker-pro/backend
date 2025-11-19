from django.db.models.signals import post_save
from django.dispatch import receiver

from inquiries.tasks import notify_limit_reached
from premium import models


@receiver(post_save, sender=models.PremiumInquiriesProduct)
def post_save_premium_inquiries_product(sender, instance, created, **kwargs):
    """
    Signal to handle actions after a premium inquiries product is saved.
    """
    if not created:
        old_instance = models.PremiumInquiriesProduct.objects.get(pk=instance.pk)

        if (
            old_instance.current_counter < instance.current_counter
            and instance.current_counter == models.PremiumInquiriesProduct.INQUIRY_LIMIT
        ):
            notify_limit_reached.delay(instance.user_inquiry.pk)

