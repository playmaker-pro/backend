from datetime import timedelta
from typing import Any, Optional, Type

from django.db.models.base import ModelBase
from django.dispatch import receiver
from django.utils import timezone

from inquiries.models import InquiryRequest
from inquiries.signals import (
    inquiry_accepted,
    inquiry_pool_exhausted,
    inquiry_rejected,
    inquiry_reminder,
    inquiry_restored,
    inquiry_sent,
)
from notifications.models import Notification
from notifications.services import NotificationService


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


@receiver(inquiry_pool_exhausted)
def handle_inquiry_pool_exhausted(sender, **kwargs) -> None:
    """
    Signal handler for when a user's inquiry pool is exhausted.

    This function is triggered by a signal when a user's available inquiries reach zero. It checks if
    a notification for exhausting the inquiry pool has already been sent to the user in the last month.
    If not, it sends a new notification to inform the user that their inquiry pool is depleted.
    """
    user = kwargs.get("user")
    if user:
        # Calculate the cutoff date for a month ago
        one_month_ago = timezone.now() - timedelta(days=30)

        # Check if a 'query_pool_exhausted' notification has been sent in the last month
        recent_notification_exists = Notification.objects.filter(
            user=user,
            event_type="query_pool_exhausted",
            created_at__gte=one_month_ago,
        ).exists()

        # If no recent notification exists, send a new one
        if not recent_notification_exists:
            NotificationService.create_user_associated_notification(
                user=user,
                event_type="query_pool_exhausted",
                notification_type="BI",
            )


@receiver(inquiry_restored)
def handle_inquiry_restored(sender, **kwargs) -> None:
    """
    Handles the restoration of an inquiry request to a user's pool and sends a notification.

    This function is called when an inquiry request is restored to the sender's inquiry pool, usually because
    it did not receive a response within a certain time frame. The function then sends a notification to the
    user to inform them of the increase in their inquiry pool.
    """
    inquiry_request = kwargs.get("inquiry_request")
    if inquiry_request:
        NotificationService.create_user_associated_notification(
            user=inquiry_request.sender,
            event_type="inquiry_request_restored",
            notification_type="BI",
        )


@receiver(inquiry_reminder)
def handle_inquiry_reminder(sender, **kwargs) -> None:
    """
    Signal handler for reminding recipients about outstanding inquiries.

    Retrieves the inquiry request from the signal's keyword arguments
    and sends a reminder notification to the recipient.
    """
    inquiry_request = kwargs.get("inquiry_request")
    if inquiry_request:
        NotificationService.create_user_associated_notification(
            user=inquiry_request.recipient,
            event_type="pending_inquiry_decision",
            notification_type="BI",
        )
