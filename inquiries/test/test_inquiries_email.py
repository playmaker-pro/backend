from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase

from utils.factories.inquiry_factories import InquiryRequestFactory

User = get_user_model()


class TestSendEmails(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(email="user1@test.xyz")
        self.user2 = User.objects.create(email="user2@test.xyz")
        self.inquiry_request = InquiryRequestFactory(
            sender=self.user1, recipient=self.user2
        )
        mail.outbox.clear()
        self.inquiry_request.send()
        self.inquiry_request.save()

    def test_send_email_on_send_request(self) -> None:
        """Send email to recipient on new request"""
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [self.user2.inquiry_contact._email]

    def test_send_email_on_accepted_request(self) -> None:
        """Send email to sender on accept request"""
        self.inquiry_request.accept()
        self.inquiry_request.save()
        assert len(mail.outbox) == 2
        assert mail.outbox[1].to == [self.user1.inquiry_contact._email]

    def test_send_email_on_reject_request(self) -> None:
        """Send email to sender on reject request"""
        self.inquiry_request.reject()
        self.inquiry_request.save()
        assert len(mail.outbox) == 2
        assert mail.outbox[1].to == [self.user1.inquiry_contact._email]
