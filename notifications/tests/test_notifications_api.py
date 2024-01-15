from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from notifications.models import Notification
from utils.factories import PlayerProfileFactory
from utils.factories.notifications_factories import NotificationFactory


class UserNotificationViewTests(APITestCase):
    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.profile = PlayerProfileFactory.create(user__email="username")
        self.user = self.profile.user
        self.client.force_authenticate(user=self.user)

    def test_get_notifications_no_notifications(self) -> None:
        """
        Test the retrieval of notifications when no notifications are present.
        It checks if the response is successful and the notification list is empty.
        """
        url = reverse(
            "api:notifications:get_user_notifications",
            kwargs={"profile_uuid": self.profile.uuid},
        )
        response = self.client.get(url)
        assert response.status_code == 200
        assert len(response.data) == 0

    def test_get_notifications_with_unread(self) -> None:
        """
        Test the retrieval of notifications including unread notifications.
        It verifies the presence of expected fields in the notification data
        and the correctness of certain notification attributes.
        """
        NotificationFactory(
            user=self.user,
            event_type="sample_event",
            notification_type=Notification.NotificationType.BUILT_IN,
            details={"event_type": "accept_inquiry"},
        )
        url = reverse(
            "api:notifications:get_user_notifications",
            kwargs={"profile_uuid": self.profile.uuid},
        )
        response = self.client.get(url)
        assert response.status_code == 200
        # Check each notification
        notifications = response.data
        for notification in notifications:
            expected_fields = [
                "id",
                "redirect_url",
                "notification_type",
                "event_type",
                "content",
                "is_read",
                "created_at",
                "updated_at",
                "user",
            ]
            for field in expected_fields:
                assert field in notification
            assert notification["event_type"] == "sample_event"
            assert (
                notification["notification_type"]
                == Notification.NotificationType.BUILT_IN
            )

    def test_mark_notification_as_read(self) -> None:
        """
        Test the marking of a notification as read.
        It checks if the notification's 'is_read' field is successfully updated.
        """
        notification = NotificationFactory(user=self.user, event_type="receive_inquiry")
        url = reverse(
            "api:notifications:mark_notification_read",
            kwargs={
                "profile_uuid": self.profile.uuid,
                "notification_id": notification.id,
            },
        )
        assert notification.is_read is False
        response = self.client.patch(url)
        assert response.status_code == 200
        notification.refresh_from_db()
        assert notification.is_read is True
