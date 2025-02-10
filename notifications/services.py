import typing
import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Exists, OuterRef, Q, QuerySet
from django.utils import timezone

from external_links.models import ExternalLinksEntity, LinkSource
from inquiries.models import InquiryRequest
from notifications.models import Notification, NotificationTemplate
from profiles.models import (
    PROFILE_MODELS,
    CoachProfile,
    GuestProfile,
    ManagerProfile,
    PlayerProfile,
    ProfileVideo,
)
from profiles.services import ProfileService
from users.services import UserPreferencesService

User = get_user_model()
profile_service = ProfileService()
user_references_service = UserPreferencesService()


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
        Retrieves a combined list of notifications for a user, both general
        and profile-specific.
        """
        profile_instance = profile_service.get_profile_by_uuid(profile_uuid)
        # Fetch notifications for the given user
        user_notifications_query = Notification.objects.filter(
            user=user, content_type=None
        ).order_by("-created_at")

        # Fetch profile-specific notifications
        profile_notifications_query = Notification.objects.filter(
            user=user,
            content_type=ContentType.objects.get_for_model(profile_instance.__class__),
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
            event_type=Notification.EventType.RECEIVE_INQUIRY,
            profile_uuid=profile_uuid,
            notification_type=Notification.NotificationType.CONTACTS,
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
            event_type=Notification.EventType.ACCEPT_INQUIRY,
            notification_type=Notification.NotificationType.CONTACTS,
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
            event_type=Notification.EventType.REJECT_INQUIRY,
            notification_type=Notification.NotificationType.CONTACTS,
            extra_details={
                "inquiry_id": inquiry_request.id,
                "recipient_name": inquiry_request.recipient.display_full_name,
            },
        )


class ProfileCompletionNotificationService:
    notification_service = NotificationService()

    @staticmethod
    def can_send_notification(
        user: User, event_type: str, profile_instance=None
    ) -> bool:
        """
        Determine if a notification can be sent based on the rules.
        """
        now = timezone.now()
        one_month_ago = now - timedelta(days=30)

        # Determine the content type for the profile instance, if provided
        content_type = (
            ContentType.objects.get_for_model(profile_instance.__class__)
            if profile_instance
            else None
        )

        notifications = Notification.objects.filter(
            user=user,
            event_type=event_type,
            content_type=content_type if profile_instance else None,
        ).order_by("created_at")
        # Check if there are any notifications
        if not notifications.exists():
            return True

        # Check the read status of the latest notification
        latest_notification = notifications.last()
        if not latest_notification.is_read:
            return False

        # Check the time since the first notification
        first_notification = notifications.first()
        if first_notification.created_at > one_month_ago:
            return False

        return True

    def notify_profiles(self, profiles: list, event_type: str) -> None:
        """
        Helper method to send notifications to a list of profiles.
        """
        for profile in profiles:
            if self.can_send_notification(profile.user, event_type, profile):
                self.notification_service.create_profile_associated_notification(
                    profile.user,
                    event_type,
                    profile.uuid,
                    Notification.NotificationType.BUILT_IN,
                )
                print(f"Notification '{event_type}' created for {profile}")

    def notify_users(self, users: list, event_type: str) -> None:
        """
        Helper method to send notifications to a list of users.
        """
        for user in users:
            if self.can_send_notification(user, event_type):
                self.notification_service.create_user_associated_notification(
                    user, event_type, Notification.NotificationType.BUILT_IN
                )
                # Optionally log or print a message about the notification sent
                print(f"Notification '{event_type}' created for user {user.username}")

    def check_and_notify_for_missing_location(self) -> None:
        """
        Check and notify users who have not specified their location in
        their user preferences.
        This method iterates over users with missing location data and
        sends a notification if the conditions defined in can_send_notification
        are met.
        """
        users_to_notify = user_references_service.get_users_with_missing_location()
        self.notify_users(
            users=users_to_notify, event_type=Notification.EventType.MISSING_LOCATION
        )

    def check_and_notify_for_missing_alternative_position(self) -> None:
        """
        Check and notify player profiles that have a main position but
        are missing alternative positions.
        This method iterates over player profiles and sends a notification for those
        needing to specify alternative playing positions.
        """
        player_profiles_to_notify = PlayerProfile.objects.filter(
            player_positions__is_main=True
        ).exclude(player_positions__is_main=False)

        self.notify_profiles(
            list(player_profiles_to_notify), Notification.EventType.MISSING_ALT_POSITION
        )

    def check_and_notify_for_missing_favorite_formation(self) -> None:
        """
        Check and notify coach profiles that have not specified their
        favorite formation.
        This method iterates over coach profiles and sends a notification to those
        with missing favorite formation information.
        """
        coach_profiles_to_notify = CoachProfile.objects.filter(formation__isnull=True)

        self.notify_profiles(
            list(coach_profiles_to_notify), Notification.EventType.MISSING_FAV_FORMATION
        )

    def check_and_notify_for_incomplete_agency_data(self) -> None:
        """
        Check and notify manager profiles that have incomplete agency data.
        This method iterates over manager profiles and sends a notification to those
        with missing agency email or Transfermarkt URL.
        """
        manager_profiles_to_notify = ManagerProfile.objects.filter(
            Q(agency_email__isnull=True) | Q(agency_transfermarkt_url__isnull=True)
        )

        self.notify_profiles(
            list(manager_profiles_to_notify),
            Notification.EventType.INCOMPLETE_AGENCY_DATA,
        )

    def check_and_notify_for_missing_external_links(self) -> None:
        """
        Check and notify profiles missing external links, excluding those
        with a specific source link.
        This method iterates over various profile models, excluding GuestProfile,
        and sends notifications to profiles missing external links and not having a link
        from the 'laczynaspilka' source.
        """
        lnp_source_name = "laczynaspilka"
        lnp_source = LinkSource.objects.filter(name=lnp_source_name).first()

        profiles_missing_links = [
            profile
            for profile_model in PROFILE_MODELS
            if profile_model is not GuestProfile
            for profile in profile_model.objects.annotate(
                has_lnp_link=Exists(
                    ExternalLinksEntity.objects.filter(
                        target__id=OuterRef("external_links__id"),
                        source=lnp_source,
                    )
                )
            ).filter(has_lnp_link=False)
        ]

        self.notify_profiles(
            profiles_missing_links, Notification.EventType.MISSING_EXT_LINKS
        )

    def check_and_notify_for_missing_video(self) -> None:
        """
        Check and notify profiles that do not have an associated video.
        This method iterates over various profile models, excluding GuestProfile,
        and sends notifications to profiles that are missing videos.
        """
        profiles_missing_video = [
            profile
            for profile_model in PROFILE_MODELS
            if profile_model is not GuestProfile
            for profile in profile_model.objects.annotate(
                has_video=Exists(ProfileVideo.objects.filter(user=OuterRef("user")))
            ).filter(has_video=False)
        ]

        self.notify_profiles(
            profiles_missing_video, Notification.EventType.MISSING_VIDEO
        )

    def check_and_notify_for_missing_photo(self) -> None:
        """
        Check and notify users who have not uploaded a profile picture.
        This method iterates over users with missing profile pictures
        and sends a notification if the conditions defined
        in can_send_notification are met.
        """
        users_to_notify = User.objects.filter(picture="")
        self.notify_users(
            users=users_to_notify, event_type=Notification.EventType.MISSING_PHOTO
        )

    def check_and_notify_for_missing_certificate_course(self) -> None:
        """
        Check and notify users who have not provided information about
        their courses or certificates.
        This method iterates over users with missing course or certificate
        information and sends a notification if the conditions defined
        in can_send_notification are met.
        """
        users_to_notify = User.objects.filter(courses__isnull=True)
        self.notify_users(
            users=users_to_notify, event_type=Notification.EventType.MISSING_COURSE
        )
