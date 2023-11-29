import typing
import uuid

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet

from inquiries.models import InquiryRequest
from notifications.models import Notification, NotificationTemplate
from profiles.services import ProfileService

User = get_user_model()
profile_service = ProfileService()


class NotificationService:
    @staticmethod
    def mark_related_notification_as_read(
        user: User, inquiry_id: int
    ) -> typing.Optional[Notification]:
        """
        Marks a notification as read based on event type, user, and inquiry ID.
        """
        # Filter notifications based on criteria
        notification = Notification.objects.filter(
            user=user,
            details__inquiry_id=inquiry_id,
            is_read=False,
        ).first()

        # If a notification is found, mark it as read
        if notification:
            notification.is_read = True
            notification.save()
            return notification

        return None

    @staticmethod
    def create_profile_associated_notification(
        user: User,
        event_type: str,
        profile_uuid: uuid.UUID,
        notification_type: str,
        extra_details: typing.Optional[dict] = None,
    ) -> typing.Optional[Notification]:
        """
        Creates a notification linked to a specific profile.
        """
        details: dict = extra_details or {}

        try:
            # Fetch the template based on event_type
            template = NotificationTemplate.objects.get(event_type=event_type)
        except NotificationTemplate.DoesNotExist:
            # Handle the case where the template does not exist
            content: str = "You have a new notification"
        else:
            # Use the template to format the content
            content: str = template.render_content(user, details)

        try:
            profile_instance = profile_service.get_profile_by_uuid(profile_uuid)
        except ObjectDoesNotExist:
            return

        # Create the notification
        notification = Notification.objects.create(
            user=user,
            event_type=event_type,
            notification_type=notification_type,
            content=content,
            object_id=user.pk,
            content_type=ContentType.objects.get_for_model(profile_instance.__class__)
            if profile_instance
            else None,
            details=details,
        )
        return notification

    @staticmethod
    def create_user_associated_notification(
        user: User,
        event_type: str,
        notification_type: str,
        extra_details: typing.Optional[dict] = None,
    ) -> Notification:
        """
        Directly create a Notification associated with a user.
        """
        details = extra_details or {}

        try:
            # Fetch the template based on event_type
            template = NotificationTemplate.objects.get(event_type=event_type)
        except NotificationTemplate.DoesNotExist:
            content = "You have a new notification"
        else:
            # Use the template to format the content
            content = template.render_content(user, details)

        # Create the notification
        notification = Notification.objects.create(
            user=user,
            event_type=event_type,
            notification_type=notification_type,
            content=content,
            object_id=user.pk,
            details=details,
        )
        return notification

    @staticmethod
    def get_combined_notifications(
        user: User, profile_uuid: uuid.UUID, latest_only: bool = False
    ) -> typing.Tuple[QuerySet, int]:
        """
        Retrieves a combined list of notifications for a user, both general and profile-specific.
        """
        profile_instance = profile_service.get_profile_by_uuid(profile_uuid)
        # Fetch notifications for the given user
        user_notifications_query = Notification.objects.filter(
            user=user, content_type=None
        ).order_by("-created_at")

        # Fetch profile-specific notifications
        profile_notifications_query = Notification.objects.filter(
            user=user, content_type=ContentType.objects.get_for_model(profile_instance.__class__)
        ).order_by("-created_at")

        # Combine both user and profile-specific querysets
        combined_notifications = user_notifications_query | profile_notifications_query

        # Remove duplicates if any
        combined_notifications = combined_notifications.distinct()

        # Calculate unread count before slicing
        unread_count = combined_notifications.filter(is_read=False).count()

        # Limit to last 5 notifications if 'latest' parameter is provided
        if latest_only:
            combined_notifications = combined_notifications[:5]

        return combined_notifications, unread_count

    @staticmethod
    def send_inquiry_notification(
        inquiry_request: InquiryRequest, profile_uuid: typing.Optional[uuid.UUID]
    ) -> None:
        """
        Handle the notification logic when an inquiry is sent.
        """
        # Create notification for the recipient about the new inquiry
        NotificationService.create_profile_associated_notification(
            user=inquiry_request.recipient,
            event_type="receive_inquiry",
            profile_uuid=profile_uuid,
            notification_type="CO",
            extra_details={
                "inquiry_id": inquiry_request.id,
                "sender_name": inquiry_request.sender.display_full_name,
            },
        )

    @staticmethod
    def accept_inquiry_notification(inquiry_request: InquiryRequest) -> None:
        """
        Handle the notification logic when an inquiry is accepted.
        """
        # Create notification for the sender about the inquiry acceptance
        NotificationService.create_user_associated_notification(
            user=inquiry_request.sender,
            event_type="accept_inquiry",
            notification_type="CO",
            extra_details={
                "inquiry_id": inquiry_request.id,
                "recipient_name": inquiry_request.recipient.display_full_name,
            },
        )

    @staticmethod
    def reject_inquiry_notification(inquiry_request: InquiryRequest) -> None:
        """
        Handle the notification logic when an inquiry is rejected.
        """
        # Create notification for the sender about the inquiry rejection
        NotificationService.create_user_associated_notification(
            user=inquiry_request.sender,
            event_type="reject_inquiry",
            notification_type="CO",
            extra_details={
                "inquiry_id": inquiry_request.id,
                "recipient_name": inquiry_request.recipient.display_full_name,
            },
        )
