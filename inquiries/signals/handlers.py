from typing import Any, Optional, Type

from django.db.models.base import ModelBase
from django.dispatch import receiver

from inquiries.models import InquiryRequest
from notifications.services import NotificationService

from . import inquiry_accepted, inquiry_rejected, inquiry_sent


@receiver(inquiry_sent)
def handle_inquiry_sent(sender: Type[ModelBase], **kwargs: Any) -> None:
    """
    Signal handler for when an inquiry is sent.

    Retrieves the inquiry request and profile UUID from the signal's keyword arguments
    and calls the notification service to handle the sent inquiry notification.
    """
    inquiry_request: Optional[InquiryRequest] = kwargs.get("inquiry_request")
    profile_uuid: Optional[str] = kwargs.get("profile_uuid")
    NotificationService.send_inquiry_notification(inquiry_request, profile_uuid)


@receiver(inquiry_accepted)
def handle_inquiry_accepted(sender: Type[ModelBase], **kwargs: Any) -> None:
    """
    Signal handler for when an inquiry is accepted.

    Retrieves the inquiry request from the signal's keyword arguments
    and calls the notification service to handle the acceptance notification.
    """
    inquiry_request: Optional[InquiryRequest] = kwargs.get("inquiry_request")
    NotificationService.accept_inquiry_notification(inquiry_request)
    # Also mark related notifications as read
    NotificationService.mark_related_notification_as_read(
        user=inquiry_request.recipient, inquiry_id=inquiry_request.id
    )


@receiver(inquiry_rejected)
def handle_inquiry_rejected(sender: Type[ModelBase], **kwargs: Any) -> None:
    """
    Signal handler for when an inquiry is rejected.

    Retrieves the inquiry request from the signal's keyword arguments
    and calls the notification service to handle the rejection notification.
    """
    inquiry_request: Optional[InquiryRequest] = kwargs.get("inquiry_request")
    NotificationService.reject_inquiry_notification(inquiry_request)
    # Also mark related notifications as read
    NotificationService.mark_related_notification_as_read(
        user=inquiry_request.recipient, inquiry_id=inquiry_request.id
    )
