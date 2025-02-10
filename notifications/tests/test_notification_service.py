import datetime
from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.utils import timezone
from parameterized import parameterized

from notifications.models import Notification
from notifications.services import (
    NotificationService,
    ProfileCompletionNotificationService,
)
from utils.factories import (
    CityFactory,
    CoachProfileFactory,
    CourseFactory,
    ManagerProfileFactory,
    PlayerProfileFactory,
    ProfileVideoFactory,
    UserFactory,
)
from utils.factories.external_links_factories import (
    ExternalLinksEntityFactory,
    ExternalLinksFactory,
    LinkSourceFactory,
)
from utils.factories.notifications_factories import NotificationFactory

complete_notification_service = ProfileCompletionNotificationService()


class NotificationServiceTests(TestCase):
    def setUp(self) -> None:
        self.profile = PlayerProfileFactory.create(
            user__email="username", user__userpreferences={"gender": "M"}
        )
        self.user = self.profile.user

    def test_mark_related_notification_as_read(self) -> None:
        """
        Test if a notification is correctly marked as read when associated
        with a specific inquiry.
        """

        NotificationFactory.create(
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
        Test if the service correctly combines user-specific and
        profile-specific notifications.
        """
        NotificationFactory.create(
            user=self.user,
            event_type="event1",
            object_id=self.user.pk,
        )
        profile_content_type = ContentType.objects.get_for_model(self.profile.__class__)
        NotificationFactory.create(
            user=self.user,
            event_type="event2",
            object_id=self.user.pk,
            content_type=profile_content_type,
        )

        notifications = NotificationService.get_combined_notifications(
            user=self.user, profile_uuid=self.profile.uuid
        )

        assert len(notifications) == 2
        assert any(n.user == self.user for n in notifications[0])


class ProfileCompletionNotificationServiceTests(TestCase):
    def setUp(self) -> None:
        # Set up two users
        self.user_not_notify = UserFactory(picture="picture")
        self.user = UserFactory(picture=None)

        self.profile_not_notify = PlayerProfileFactory(user=self.user_not_notify)

        # Setting UserPreferences for both users
        # 'user_not_notify' gets a specific city, 'user' gets no localization
        city_instance = CityFactory()
        user_preferences = self.user.userpreferences
        user_preferences.localization = None
        user_preferences.save()
        user_preferences_not_notify = self.user_not_notify.userpreferences
        user_preferences_not_notify.localization = city_instance
        user_preferences_not_notify.save()

        # User 'user_not_notify' has external links including 'laczynaspilka'
        laczynaspilka_source = LinkSourceFactory(name="laczynaspilka")
        external_links_with_laczynaspilka = ExternalLinksFactory()
        ExternalLinksEntityFactory(
            target=external_links_with_laczynaspilka, source=laczynaspilka_source
        )
        self.profile_not_notify.external_links = external_links_with_laczynaspilka
        self.profile_not_notify.save()

        # User 'user' lacks external links and will be the target for notification
        self.profile = PlayerProfileFactory(
            user=self.user, player_positions__is_main=True
        )

        # Additional setup for 'user_not_notify' - videos and courses
        ProfileVideoFactory(user=self.user_not_notify)
        CourseFactory(owner=self.user_not_notify)

        self.coach_with_formation = CoachProfileFactory(formation="4-4-2")
        self.coach_without_formation = CoachProfileFactory(formation=None)

        self.manager_with_complete_data = ManagerProfileFactory(
            agency_email="agency@example.com",
            agency_transfermarkt_url="http://transfermarkt.example.com",
        )
        self.manager_with_missing_email = ManagerProfileFactory(
            agency_email=None,
            agency_transfermarkt_url="http://transfermarkt.example.com",
        )
        self.manager_with_missing_url = ManagerProfileFactory(
            agency_email="agency@example.com", agency_transfermarkt_url=None
        )
        self.manager_with_both_missing = ManagerProfileFactory(
            agency_email=None, agency_transfermarkt_url=None
        )

    def test_can_send_notification(self) -> None:
        """
        Test to verify that the `can_send_notification` method correctly allows
        or blocks notifications.
        It first asserts that a notification can be sent when there is no prior
        notification for a given event type.
        Then, it creates a notification and checks that a new notification for
        the same event type cannot be sent.
        """
        assert ProfileCompletionNotificationService.can_send_notification(
            self.user, "missing_location"
        )
        NotificationFactory.create(
            user=self.user,
            event_type="test_event",
            is_read=False,
            details={"inquiry_id": 123},
            object_id=self.user.pk,
            created_at=datetime.datetime.now(),
            content_type=None,
        )
        assert not ProfileCompletionNotificationService.can_send_notification(
            self.user, "test_event"
        )

    def test_notify_profile(self) -> None:
        """
        Test to verify that a notification is correctly sent to a user's profile.
        It asserts that no notification exists initially, sends a notification,
        and then asserts that a notification has been created.
        """

        notification_before_send = Notification.objects.filter(user=self.user).exists()
        assert not notification_before_send
        complete_notification_service.notify_profiles([self.profile], "test_event")
        notification_after_send = Notification.objects.filter(user=self.user).exists()
        assert notification_after_send

    @parameterized.expand(
        [
            (
                Notification.EventType.MISSING_LOCATION,
                complete_notification_service.check_and_notify_for_missing_location,
            ),
            (
                Notification.EventType.MISSING_ALT_POSITION,
                complete_notification_service.check_and_notify_for_missing_alternative_position,  # noqa:  E501
            ),
            (
                Notification.EventType.MISSING_EXT_LINKS,
                complete_notification_service.check_and_notify_for_missing_external_links,  # noqa:  E501
            ),
            (
                Notification.EventType.MISSING_COURSE,
                complete_notification_service.check_and_notify_for_missing_certificate_course,  # noqa:  E501
            ),
            (
                Notification.EventType.MISSING_PHOTO,
                complete_notification_service.check_and_notify_for_missing_photo,
            ),
            (
                Notification.EventType.MISSING_VIDEO,
                complete_notification_service.check_and_notify_for_missing_video,
            ),
        ]
    )
    def test_notify_missing_field(self, event_type, action) -> None:
        """
        Parameterized test to verify that notifications are correctly sent for
        various missing profile fields.
        It iterates over different event types and corresponding notification methods,
        asserting that notifications are sent as expected.
        """
        notification_before_send = Notification.objects.filter(
            user=self.user, event_type=event_type
        ).exists()
        notification_before_send_2 = Notification.objects.filter(
            user=self.user_not_notify, event_type=event_type
        ).exists()
        assert notification_before_send is False
        assert notification_before_send_2 is False
        action()
        notification_after_send = Notification.objects.filter(
            user=self.user, event_type=event_type
        ).exists()
        notification_after_send_2 = Notification.objects.filter(
            user=self.user_not_notify, event_type=event_type
        ).exists()
        assert notification_after_send
        assert not notification_after_send_2

    def test_notify_missing_favorite_formation(self) -> None:
        """
        Test to verify that coach profiles without a favorite formation
        receive a notification.
        It asserts that coaches with a formation set do not receive a notification,
        while those without a formation do.
        """
        complete_notification_service.check_and_notify_for_missing_favorite_formation()

        # Verifying notification only for coach without formation
        notification_for_coach_with_formation = Notification.objects.filter(
            user=self.coach_with_formation.user,
            event_type=Notification.EventType.MISSING_FAV_FORMATION,
        ).exists()
        notification_for_coach_without_formation = Notification.objects.filter(
            user=self.coach_without_formation.user,
            event_type=Notification.EventType.MISSING_FAV_FORMATION,
        ).exists()

        assert not notification_for_coach_with_formation
        assert notification_for_coach_without_formation

    @parameterized.expand(
        [
            ("manager_with_complete_data", False),
            ("manager_with_missing_email", True),
            ("manager_with_missing_url", True),
            ("manager_with_both_missing", True),
        ]
    )
    def test_notify_incomplete_agency_data(self, manager_type, expected_result) -> None:
        """
        Parameterized test to verify that manager profiles with incomplete agency
        data receive notifications.
        It checks different scenarios (complete data, missing email, missing URL,
        both missing) and asserts if notifications are created as expected.
        """
        manager = getattr(self, manager_type)
        complete_notification_service.check_and_notify_for_incomplete_agency_data()

        # Assertions
        notification_exists = Notification.objects.filter(
            user=manager.user,
            event_type=Notification.EventType.INCOMPLETE_AGENCY_DATA,
        ).exists()

        assert (
            notification_exists == expected_result
        ), f"Assertion for {manager_type} failed."

    def test_can_send_notification_with_old_read_notification(self) -> None:
        """
        Test to verify that a user can receive a notification if the last notification
        (for the same event type) is older than 30 days and marked as read.
        """
        # Create a notification that's older than 30 days and marked as read
        NotificationFactory(
            user=self.user,
            event_type="test_event",
            created_at=timezone.now() - timedelta(days=31),
            is_read=True,
        )

        # Test can_send_notification for this user and event type
        can_send = ProfileCompletionNotificationService.can_send_notification(
            self.user, "test_event"
        )

        assert can_send, (
            "Should be able to send notification if the last one "
            "is older than 30 days and read"
        )

    def test_can_send_notification_with_old_unread_notification(self) -> None:
        """
        Test to verify that a user cannot receive a new notification if the last
        notification (for the same event type) is older than 30 days but still unread.
        """
        # Create an unread notification that's older than 30 days
        NotificationFactory(
            user=self.user,
            event_type="test_event_outdated",
            created_at=timezone.now() - timedelta(days=30),
            is_read=False,
            content_type=None,
        )

        # Test can_send_notification for this user and event type
        can_send = ProfileCompletionNotificationService.can_send_notification(
            self.user, "test_event_outdated"
        )

        assert not can_send, (
            "Should not be able to send notification if the last one "
            "is older than 30 days but not read"
        )
