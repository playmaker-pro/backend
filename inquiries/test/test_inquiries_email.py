from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.utils import timezone

from inquiries.errors import ForbiddenLogAction
from inquiries.models import InquiryLogMessage, UserInquiry
from mailing.models import EmailTemplate as _EmailTemplate
from utils.factories import UserFactory
from utils.factories.inquiry_factories import InquiryRequestFactory
from utils.factories.mailing_factories import (
    UserEmailOutboxFactory as _UserEmailOutboxFactory,
)

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

    def test_send_email_on_limit_reached(self) -> None:
        """Send email to user if he reached inquiry requests limit"""
        self._purge_outbox()
        self.user1.userinquiry.counter = 5
        self.user1.userinquiry.save()

        limit_reached = UserInquiry.objects.limit_reached()
        assert limit_reached.count() == 1, limit_reached.first().user == self.user1

        self.user1.userinquiry.notify_about_limit(force=True)

        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [self.user1.inquiry_contact._email]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "last_user_outbox_sent_email_date,current_date,expected",
    [
        (timezone.datetime(2023, 6, 1), timezone.datetime(2023, 12, 1), True),
        (timezone.datetime(2023, 7, 1), timezone.datetime(2023, 11, 1), False),
        (timezone.datetime(2023, 7, 1), timezone.datetime(2025, 11, 1), True),
        (timezone.datetime(2023, 12, 1), timezone.datetime(2025, 7, 1), True),
        (timezone.datetime(2023, 12, 2), timezone.datetime(2023, 12, 6), False),
        (timezone.datetime(2023, 4, 1), timezone.datetime(2023, 6, 1), True),
        (timezone.datetime(2023, 4, 1), timezone.datetime(2025, 4, 1), True),
        (timezone.datetime(2023, 4, 1), timezone.datetime(2023, 5, 1), False),
        (timezone.datetime(2023, 4, 1), timezone.datetime(2025, 4, 1), True),
        (timezone.datetime(2022, 12, 3), timezone.datetime(2023, 6, 1), True),
        (timezone.datetime(2022, 12, 3), timezone.datetime(2023, 4, 1), False),
        (timezone.datetime(2022, 12, 3), timezone.datetime(2026, 4, 1), True),
        (None, timezone.datetime(2023, 6, 1), True),
    ],
)
def test_multiple_cases_for_mailing_about_reaching_limit(
    last_user_outbox_sent_email_date, current_date, expected, user_inquiry_on_limit
) -> None:
    """
    Test multiple cases for mailing about reaching limit.
    Ensure that user can receive email once again on specific date.
    """
    if last_user_outbox_sent_email_date:
        ueo = _UserEmailOutboxFactory.create(
            recipient=user_inquiry_on_limit.user.email,
            email_type=_EmailTemplate.EmailType.INQUIRY_LIMIT,
        )
        ueo.sent_date = last_user_outbox_sent_email_date
        ueo.save()

    with patch("django.utils.timezone.now") as mock_datetime_now:
        mock_datetime_now.return_value = current_date

        assert (
            _EmailTemplate.objects.can_sent_inquiry_limit_reached_email(
                user_inquiry_on_limit.user
            )
            is expected
        )
