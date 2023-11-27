from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase

from inquiries.errors import ForbiddenLogAction
from inquiries.models import InquiryLogMessage
from utils.factories import UserFactory
from utils.factories.inquiry_factories import InquiryRequestFactory

User = get_user_model()


class TestSendEmails(TestCase):
    def setUp(self):
        self.user1 = UserFactory.create()
        self.user2 = UserFactory.create()
        self.inquiry_request = InquiryRequestFactory(
            sender=self.user1, recipient=self.user2
        )

    def _purge_outbox(self) -> None:
        """Delete all mails from outbox to have empty playground for tests."""
        mail.outbox.clear()

    def test_send_email_on_send_request(self) -> None:
        """Send email to recipient on new request"""
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [self.user2.inquiry_contact._email]

    def test_send_email_on_accepted_request(self) -> None:
        """Send email to sender on accept request"""
        self._purge_outbox()
        self.inquiry_request.accept()
        self.inquiry_request.save()
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [self.user1.inquiry_contact._email]

    def test_send_email_on_reject_request(self) -> None:
        """Send email to sender on reject request"""
        self._purge_outbox()
        self.inquiry_request.reject()
        self.inquiry_request.save()
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [self.user1.inquiry_contact._email]

    def test_send_email_on_outdated_request_to_sender(self) -> None:
        """Send email to sender on outdated request"""
        self._purge_outbox()
        assert len(mail.outbox) == 0

        _3days_back = self.inquiry_request.created_at - timedelta(days=4, hours=1)
        _6days_back = self.inquiry_request.created_at - timedelta(days=6, hours=1)
        _any_other_time = self.inquiry_request.created_at - timedelta(days=100)

        assert not self.inquiry_request.logs.filter(
            message__log_type=InquiryLogMessage.MessageType.OUTDATED_REMINDER
        ).exists()

        self.inquiry_request.created_at = _3days_back
        self.inquiry_request.save()
        self.inquiry_request.refresh_from_db()
        assert (
            self.inquiry_request.__class__.objects.to_remind_recipient_about_outdated().count()  # noqa
            == 1
        )

        self.inquiry_request.notify_recipient_about_outdated()
        self.inquiry_request.refresh_from_db()

        assert (
            self.inquiry_request.__class__.objects.to_remind_recipient_about_outdated().count()  # noqa
            == 0
        )
        assert (
            self.inquiry_request.logs.filter(
                message__log_type=InquiryLogMessage.MessageType.OUTDATED_REMINDER
            ).count()
            == 1
        )
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [self.user2.inquiry_contact._email]

        # second time should not be sent without changing date
        with pytest.raises(ForbiddenLogAction):
            self.inquiry_request.notify_recipient_about_outdated()

        self.inquiry_request.created_at = _6days_back
        self.inquiry_request.save()

        assert (
            self.inquiry_request.__class__.objects.to_remind_recipient_about_outdated().count()  # noqa
            == 1
        )

        self.inquiry_request.notify_recipient_about_outdated()
        self.inquiry_request.refresh_from_db()

        assert len(mail.outbox) == 2
        assert mail.outbox[1].to == [self.user2.inquiry_contact._email]
        assert (
            self.inquiry_request.logs.filter(
                message__log_type=InquiryLogMessage.MessageType.OUTDATED_REMINDER
            ).count()
            == 2
        )

        self.inquiry_request.created_at = _any_other_time
        self.inquiry_request.save()

        # recipient should not be notified anymore
        with pytest.raises(ForbiddenLogAction):
            self.inquiry_request.notify_recipient_about_outdated()

    def test_send_email_on_reward_sender(self) -> None:
        """Send email to sender on reward sender"""
        self._purge_outbox()
        _7days_back = self.inquiry_request.created_at - timedelta(days=7, hours=1)
        self.inquiry_request.created_at = _7days_back
        self.inquiry_request.save()
        self.inquiry_request.reward_sender()

        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [self.user1.inquiry_contact._email]

        # Assert we can't reward sender twice
        with pytest.raises(ForbiddenLogAction):
            self.inquiry_request.reward_sender()
