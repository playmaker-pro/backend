from django.db.models.signals import post_save
from django.dispatch import receiver

from inquiries.constants import InquiryLogType
from inquiries.models import InquiryRequest, UserInquiry, UserInquiryLog
from inquiries.tasks import notify_limit_reached, send_inquiry_update_email


@receiver(post_save, sender=UserInquiry)
def post_save_user_inquiry(sender, instance, created, **kwargs):
    """
    Signal handler to set the display status of a user inquiry
    if the first name and last name are the same.
    """
    if not created and instance.counter == instance.limit:
        notify_limit_reached.delay(instance.pk)


@receiver(post_save, sender=UserInquiryLog)
def post_save_user_inquiry_log(sender, instance, created, **kwargs):
    """
    Signal handler to perform actions after a user inquiry is saved.
    """
    if created and instance.send_mail:
        send_inquiry_update_email.delay(instance.pk)


@receiver(post_save, sender=InquiryRequest)
def post_save_inquiry_request(sender, instance, created, **kwargs):
    """
    Signal handler to perform actions after an inquiry request is saved.
    This can include notifying the recipient or logging the action.
    """
    if created:
        instance.sender.userinquiry.increment()
        instance.create_log_for_recipient(InquiryLogType.NEW)
