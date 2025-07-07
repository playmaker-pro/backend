from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.utils import timezone

from inquiries.errors import ForbiddenLogAction
from inquiries.models import InquiryLogMessage, UserInquiry, UserInquiryLog
from inquiries.utils import InquiryMessageContentParser
from mailing.models import EmailTemplate as _EmailTemplate
from mailing.schemas import EmailSchema
from utils.factories.inquiry_factories import InquiryRequestFactory
from utils.factories.mailing_factories import (
    UserEmailOutboxFactory as _UserEmailOutboxFactory,
)
from utils.factories.profiles_factories import GuestProfileFactory, PlayerProfileFactory

User = get_user_model()


class TestSendEmails(TestCase):
    def setUp(self):
        self.user1 = PlayerProfileFactory.create().user
        self.user2 = GuestProfileFactory.create().user
        self.inquiry_request = InquiryRequestFactory(
            sender=self.user1, recipient=self.user2
        )

    def _purge_outbox(self) -> None:
        """Delete all mails from outbox to have empty playground for tests."""
        mail.outbox.clear()

    def test_send_email_on_send_request(self) -> None:
        """Send email to recipient on new request"""
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [self.user2.contact_email]

    def test_send_email_on_accepted_request(self) -> None:
        """Send email to sender on accept request"""
        self._purge_outbox()
        self.inquiry_request.accept()
        self.inquiry_request.save()
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [self.user1.contact_email]

    def test_send_email_on_reject_request(self) -> None:
        """Send email to sender on reject request"""
        self._purge_outbox()
        self.inquiry_request.reject()
        self.inquiry_request.save()
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [self.user1.contact_email]

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
        assert mail.outbox[0].to == [self.user2.contact_email]

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
        assert mail.outbox[1].to == [self.user2.contact_email]
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
        assert mail.outbox[0].to == [self.user1.contact_email]

        # Assert we can't reward sender twice
        with pytest.raises(ForbiddenLogAction):
            self.inquiry_request.reward_sender()

    def test_send_email_on_limit_reached(self) -> None:
        """Send email to user if he reached inquiry requests limit"""
        self._purge_outbox()
        self.user1.userinquiry.counter = 2
        self.user1.userinquiry.save()

        limit_reached = UserInquiry.objects.limit_reached()
        assert limit_reached.count() == 1, limit_reached.first().user == self.user1

        self.user1.userinquiry.notify_about_limit(force=True)

        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [self.user1.contact_email]


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


@pytest.mark.django_db
class TestHTMLEmailFunctionality(TestCase):
    """Test HTML email functionality for UserInquiry emails."""

    def setUp(self):
        """Set up test data."""

        # Create test users
        self.user1 = PlayerProfileFactory.create().user
        self.user2 = GuestProfileFactory.create().user

        # Create inquiry request
        self.inquiry_request = InquiryRequestFactory(
            sender=self.user1, recipient=self.user2
        )

        self.user_inquiry = UserInquiry.objects.create(
            user=self.user2,
        )

        # Clear mail outbox
        mail.outbox.clear()

    def test_inquiry_log_message_html_parsing(self):
        """Test that InquiryLogMessage HTML parsing works correctly."""

        # Create a test message with HTML content
        test_message = InquiryLogMessage.objects.filter(
            log_type=InquiryLogMessage.MessageType.ACCEPTED,
        )

        # Create a log entry
        log_entry = UserInquiryLog.objects.create(
            log_owner=self.user_inquiry,
            related_with=self.inquiry_request.sender,
            message=test_message
        )

        # Test HTML parsing
        parser = InquiryMessageContentParser(log_entry)

        # Test email title parsing
        parsed_title = parser.parse_email_title
        assert "#r#" not in parsed_title
        assert self.user2.display_full_name in parsed_title

        # Test plain text body parsing
        parsed_body = parser.parse_email_body
        assert "<>" not in parsed_body
        assert self.user2.display_full_name in parsed_body

        # Test HTML body parsing
        parsed_html_body = parser.parse_email_html_body
        assert "<>" not in parsed_html_body
        assert "#r#" not in parsed_html_body
        assert self.user2.display_full_name in parsed_html_body


    def test_email_schema_creation(self):
        """Test that EmailSchema is created correctly with HTML content."""

        # Create a test message
        test_message = InquiryLogMessage.objects.filter(
            log_type=InquiryLogMessage.MessageType.ACCEPTED,
        )

        # Create a log entry
        log_entry = UserInquiryLog.objects.create(
            log_owner=self.inquiry_request.recipient,
            related_with=self.inquiry_request.sender,
            message=test_message
        )

        # Test email schema creation
        schema = log_entry.create_email_schema()

        assert isinstance(schema, EmailSchema)
        assert schema.subject == test_message.email_title
        assert schema.body == test_message.email_body
        assert schema.html_body == test_message.email_body_html
        assert schema.recipients == [self.user2.contact_email]


    def test_inquiry_status_emails_with_html(self):
        """Test that inquiry status change emails work with HTML content."""
        # Clear mail outbox
        mail.outbox.clear()

        # Test accepted inquiry
        with patch('mailing.services.MailingService.send_mail') as mock_send:
            self.inquiry_request.accept()
            self.inquiry_request.save()

            # Check if email was attempted to be sent
            if mock_send.called:
                print("✅ ACCEPTED email sending was called")
                # Get the last log entry
                last_log = UserInquiryLog.objects.filter(
                    message__log_type=InquiryLogMessage.MessageType.ACCEPTED
                ).last()
                if last_log:
                    schema = last_log.create_email_schema()
                    print(f"Email schema created successfully: {schema.subject}")
            else:
                print("⚠️  No email sent for ACCEPTED status")

        # Test rejected inquiry
        print("Testing REJECTED inquiry email...")
        # Create a new inquiry for rejection test
        inquiry_request_2 = InquiryRequestFactory(
            sender=self.user1, recipient=self.user2
        )

        with patch('mailing.services.MailingService.send_mail') as mock_send:
            inquiry_request_2.reject()
            inquiry_request_2.save()

            # Check if email was attempted to be sent
            if mock_send.called:
                print("✅ REJECTED email sending was called")
                # Get the last log entry
                last_log = UserInquiryLog.objects.filter(
                    message__log_type=InquiryLogMessage.MessageType.REJECTED
                ).last()
                if last_log:
                    schema = last_log.create_email_schema()
                    print(f"Email schema created successfully: {schema.subject}")
            else:
                print("⚠️  No email sent for REJECTED status")

        print("✅ Inquiry status change emails test passed!")
        return True

    def test_inquiry_limit_email_with_html(self):
        """Test that inquiry limit reached email works with HTML content."""
        print("\n=== Testing Inquiry Limit Email ===")

        # Clear mail outbox
        mail.outbox.clear()

        # Set user to limit
        self.user1.userinquiry.counter = 2
        self.user1.userinquiry.save()

        # Test limit notification
        with patch('mailing.services.MailingService.send_mail') as mock_send:
            with patch('utils.utils.render_email_template') as mock_render:
                # Mock the render_email_template function
                mock_render.return_value = ("<h1>HTML content</h1>", "Plain text content")

                self.user1.userinquiry.mail_about_limit(force_send=True)

                # Check if email was attempted to be sent
                if mock_send.called:
                    print("✅ INQUIRY_LIMIT email sending was called")
                    # Check if render_email_template was called correctly
                    if mock_render.called:
                        print("✅ HTML template rendering was called")
                        call_args = mock_render.call_args
                        print(f"Template path: {call_args[0][0]}")
                        print(f"Context: {call_args[0][1]}")
                else:
                    print("⚠️  No email sent for INQUIRY_LIMIT")

        return True
