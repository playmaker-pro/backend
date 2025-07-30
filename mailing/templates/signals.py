from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from inquiries.models import UserInquiry, UserInquiryLog
from inquiries.tasks import notify_limit_reached, send_inquiry_update_email


@receiver(pre_save, sender=UserInquiry)
def pre_save_user_inquiry(sender, instance, **kwargs):
    """
    Signal handler to set the display status of a user inquiry
    if the first name and last name are the same.
    """
    if instance.counter == instance.limit:
        notify_limit_reached.delay(instance.pk)


@receiver(post_save, sender=UserInquiryLog)
def post_save_user_inquiry(sender, instance, created, **kwargs):
    """
    Signal handler to perform actions after a user inquiry is saved.
    """
    if created:
        send_inquiry_update_email.delay(instance.pk)
