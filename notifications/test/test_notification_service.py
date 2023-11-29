from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from rest_framework.test import APIClient, APITestCase

from notifications.models import Notification
from notifications.services import NotificationService
from utils.factories import PlayerProfileFactory


class NotificationServiceTests(TestCase):
    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.profile = PlayerProfileFactory.create(
            user__email="username", user__userpreferences={"gender": "M"}
        )
        self.user = self.profile.user
        self.client.force_authenticate(user=self.user)

    def test_mark_related_notification_as_read(self) -> None:
        """
        Test if a notification is correctly marked as read when associated with a specific inquiry.
        """
        Notification.objects.create(
            user=self.user,
            event_type="test_event",
            is_read=False,
            details={"inquiry_id": 123},
            object_id=self.user.pk,
        )

        marked_notification = NotificationService.mark_related_notification_as_read(
            user=self.user, inquiry_id=123
        )

        assert marked_notification is not None
        assert marked_notification.is_read

    def test_get_combined_notifications(self) -> None:
        """
        Test if the service correctly combines user-specific and profile-specific notifications.
        """
        Notification.objects.create(
            user=self.user,
            event_type="event1",
            object_id=self.user.pk,
        )
        profile_content_type = ContentType.objects.get_for_model(self.profile.__class__)
        Notification.objects.create(
            user=self.user, event_type="event2", object_id=self.user.pk, content_type=profile_content_type
        )

        notifications = NotificationService.get_combined_notifications(
            user=self.user, profile_uuid=self.profile.uuid
        )

        assert len(notifications) == 2
        assert any(n.user == self.user for n in notifications[0])
