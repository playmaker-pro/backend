from django.dispatch import receiver
from django.test import TestCase
from django.utils import timezone

from inquiries.models import InquiryRequest
from inquiries.signals import (
    inquiry_accepted,
    inquiry_rejected,
    inquiry_reminder,
    inquiry_restored,
    inquiry_sent,
)
from notifications.models import Notification
from utils.factories import GuestProfileFactory
from utils.factories.inquiry_factories import InquiryRequestFactory


class InquirySignalTests(TestCase):
    def setUp(self):
        self.inquiry_request = InquiryRequestFactory()

        self.sender, self.recipient = (
            self.inquiry_request.sender,
            self.inquiry_request.recipient,
        )
        GuestProfileFactory.create(user=self.recipient)
        self.sender.save()
        self.recipient.save()

    def test_inquiry_sent_signal(self):
        """
        Test if the 'inquiry_sent' signal is correctly triggered when an inquiry
        is sent.
        """

        # Connect a mock receiver to the signal
        @receiver(inquiry_sent)
        def mock_receiver(sender, **kwargs):
            self.signal_triggered = True

        self.signal_triggered = False

        # Manually create and save an inquiry instance to trigger the save
        # method correctly
        inquiry = InquiryRequestFactory(sender=self.sender, recipient=self.recipient)
        inquiry.save(recipient_profile_uuid=self.recipient.profile.uuid)

        # Assert that the signal was triggered
        assert self.signal_triggered

    def test_inquiry_accepted_signal(self):
        """
        Test if the 'inquiry_accepted' signal is correctly triggered when an inquiry
        is accepted.
        """

        # Similar setup as above
        @receiver(inquiry_accepted)
        def mock_receiver(sender, **kwargs):
            self.signal_triggered = True

        self.signal_triggered = False

        # Create an inquiry and then trigger the accept signal
        inquiry = InquiryRequestFactory(sender=self.sender, recipient=self.recipient)
        inquiry.accept()

        # Assert that the signal was triggered
        assert self.signal_triggered

    def test_inquiry_rejected_signal(self):
        """
        Test if the 'inquiry_rejected' signal is correctly triggered when an inquiry
        is rejected.
        """

        @receiver(inquiry_rejected)
        def mock_receiver(sender, **kwargs):
            self.signal_triggered = True

        self.signal_triggered = False

        # Create an inquiry and then trigger the reject signal
        inquiry = InquiryRequestFactory(sender=self.sender, recipient=self.recipient)
        inquiry.reject()
        # Assert that the signal was triggered
        assert self.signal_triggered

    def test_inquiry_pool_exhausted_signal(self):
        """
        Tests the signal for when a user's inquiry pool is exhausted.

        This test simulates a user sending inquiries until their pool is exhausted.
        It then checks if the corresponding notification for the pool exhaustion
        is created as expected.
        """
        # Set the sender's inquiry count just below the limit
        self.sender.userinquiry.counter = self.sender.userinquiry.limit - 1
        self.sender.userinquiry.save()

        # Create an inquiry request that should exhaust the inquiry pool
        InquiryRequestFactory(sender=self.sender, recipient=self.recipient)

        # The signal should be triggered automatically here
        # Assert that a notification was created
        notification_exists = Notification.objects.filter(
            user=self.sender,
            event_type=Notification.EventType.QUERY_POOL_EXHAUSTED,
            created_at__gte=timezone.now() - timezone.timedelta(days=30),
        ).exists()
        assert notification_exists

    def test_inquiry_reminder_signal(self):
        """
        Tests the signal for sending a reminder to a recipient about an outstanding
        inquiry.

        This test creates an inquiry request and triggers a reminder signal.
        It then checks if a notification is created for the recipient to remind
        them about the pending inquiry.
        """
        # Create an inquiry request
        inquiry_request = InquiryRequestFactory(
            sender=self.sender, recipient=self.recipient
        )
        inquiry_request.save()
        # Trigger signal
        inquiry_reminder.send(sender=InquiryRequest, inquiry_request=inquiry_request)
        # Assert that a notification was created for the recipient
        notification_exists = Notification.objects.filter(
            user=self.recipient,
            event_type=Notification.EventType.PENDING_INQUIRY_DECISION,
        ).exists()
        assert notification_exists

    def test_inquiry_restored_signal(self):
        """
        Tests the signal for when an inquiry request is restored to a sender's
        inquiry pool.

        This test simulates the restoration of an inquiry request back to the sender's
        inquiry pool, typically due to a lack of response from the recipient.
        It checks if a notification is created for the sender informing them about
        the restored inquiry.
        """
        # Create an inquiry request
        inquiry_request = InquiryRequestFactory(
            sender=self.sender, recipient=self.recipient
        )
        inquiry_request.save()

        # Trigger signal
        inquiry_restored.send(sender=InquiryRequest, inquiry_request=inquiry_request)

        # Assert that a notification was created for the sender
        notification_exists = Notification.objects.filter(
            user=self.sender,
            event_type=Notification.EventType.INQUIRY_REQUEST_RESTORED,
        ).exists()
        self.assertTrue(notification_exists)
