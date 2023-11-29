from django.dispatch import receiver
from django.test import TestCase

from inquiries.models import InquiryRequest
from inquiries.signals import inquiry_accepted, inquiry_rejected, inquiry_sent
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
        Test if the 'inquiry_sent' signal is correctly triggered when an inquiry is sent.
        """

        # Connect a mock receiver to the signal
        @receiver(inquiry_sent)
        def mock_receiver(sender, **kwargs):
            self.signal_triggered = True

        self.signal_triggered = False

        # Manually create and save an inquiry instance to trigger the save method correctly
        inquiry = InquiryRequest(sender=self.sender, recipient=self.recipient)
        inquiry.save(recipient_profile_uuid=self.recipient.profile.uuid)

        # Assert that the signal was triggered
        assert self.signal_triggered

    def test_inquiry_accepted_signal(self):
        """
        Test if the 'inquiry_accepted' signal is correctly triggered when an inquiry is accepted.
        """

        # Similar setup as above
        @receiver(inquiry_accepted)
        def mock_receiver(sender, **kwargs):
            self.signal_triggered = True

        self.signal_triggered = False

        # Create an inquiry and then trigger the accept signal
        inquiry = InquiryRequest.objects.create(
            sender=self.sender, recipient=self.recipient
        )
        inquiry.accept()

        # Assert that the signal was triggered
        assert self.signal_triggered

    def test_inquiry_rejected_signal(self):
        """
        Test if the 'inquiry_rejected' signal is correctly triggered when an inquiry is rejected.
        """

        @receiver(inquiry_rejected)
        def mock_receiver(sender, **kwargs):
            self.signal_triggered = True

        self.signal_triggered = False

        # Create an inquiry and then trigger the reject signal
        inquiry = InquiryRequest.objects.create(
            sender=self.sender, recipient=self.recipient
        )
        inquiry.reject()
        # Assert that the signal was triggered
        assert self.signal_triggered
