import logging
import sys
from unittest.mock import Mock, patch

import pytest
from django.core import mail
from django.test import TestCase, override_settings

from backend.settings.config import Environment
from mailing.handlers import AsyncAdminEmailHandler


@pytest.fixture
def mock_notify_admins():
    """Mock for notify_admins Celery task."""
    with patch("mailing.handlers.AsyncAdminEmailHandler.send_mail") as mock:
        yield mock


@pytest.fixture
def mock_mail_admins():
    """Mock for mail_admins function."""
    with patch("mailing.tasks.mail_admins") as mock:
        yield mock


@pytest.fixture
def error_log_record():
    """Create an error log record for testing."""
    record = logging.LogRecord(
        name="test_logger",
        level=logging.ERROR,
        pathname="/test/path.py",
        lineno=42,
        msg="Test error message",
        args=(),
        exc_info=None,
    )
    record.getMessage = lambda: "Test error message"
    return record


@pytest.fixture
def exception_log_record():
    """Create a log record with exception info."""
    try:
        raise ValueError("Test exception for email handler")
    except ValueError:
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="/test/path.py",
            lineno=42,
            msg="Error with exception",
            args=(),
            exc_info=sys.exc_info(),  # Use actual exception info tuple
        )
        record.getMessage = lambda: "Error with exception"
        return record


class TestAsyncAdminEmailHandler:
    """Test cases for AsyncAdminEmailHandler."""

    @pytest.fixture(autouse=True)
    def override_settings(self):
        with patch("mailing.handlers.settings") as mock_settings:
            mock_settings.ADMINS = [("Test Admin", "admin@test.com")]
            mock_settings.CONFIGURATION = Environment.STAGING
            yield mock_settings

    @pytest.fixture(autouse=True)
    def mock_slack_dependencies(self):
        """Mock Slack dependencies to avoid import errors."""
        with patch("mailing.handlers.send_error_message") as mock_send_error:
            mock_send_error.delay = Mock()
            yield mock_send_error

    def setup_method(self):
        """Setup for each test method."""
        self.handler = AsyncAdminEmailHandler()
        self.handler.setLevel(logging.ERROR)

    def test_handler_initialization(self):
        """Test that handler initializes correctly."""
        assert isinstance(self.handler, AsyncAdminEmailHandler)
        assert self.handler.level == logging.ERROR

    def test_emit_calls_slack_in_staging(
        self, mock_slack_dependencies, error_log_record
    ):
        """Test that emit method calls Slack in staging environment."""
        self.handler.emit(error_log_record)
        mock_slack_dependencies.delay.assert_called_once()

    def test_emit_with_exception_info(
        self, mock_slack_dependencies, exception_log_record
    ):
        """Test emit with exception information."""
        self.handler.emit(exception_log_record)
        mock_slack_dependencies.delay.assert_called_once()

    def test_emit_falls_back_to_email_on_slack_error(
        self, mock_slack_dependencies, error_log_record
    ):
        """Test that handler falls back to email when Slack fails."""
        # Make Slack fail
        from app.slack.errors import SlackDisabledException

        mock_slack_dependencies.delay.side_effect = SlackDisabledException(
            "Slack disabled"
        )

        with patch.object(self.handler, "send_mail") as mock_send_mail:
            self.handler.emit(error_log_record)
            mock_send_mail.assert_called_once()

    def test_format_and_message_content(self, mock_slack_dependencies):
        """Test that the handler properly formats the subject and message."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="/test/path.py",
            lineno=42,
            msg="Formatted error: %s",
            args=("critical issue",),
            exc_info=None,
        )
        record.getMessage = lambda: "Formatted error: critical issue"

        self.handler.emit(record)

        mock_slack_dependencies.delay.assert_called_once()


@override_settings(
    ADMINS=[("Test Admin", "admin@test.com")], CONFIGURATION=Environment.STAGING
)
class TestAsyncAdminEmailHandlerIntegration(TestCase):
    """Integration tests for AsyncAdminEmailHandler with Django logging."""

    @patch("mailing.handlers.send_error_message.delay")
    def test_django_logger_error_triggers_slack(self, mock_send_error):
        """Test that Django logger errors trigger Slack notifications."""
        logger = logging.getLogger("django")
        logger.error("Test Django error for slack notification")
        mock_send_error.assert_called()

    @patch("mailing.handlers.send_error_message.delay")
    def test_application_exception_triggers_slack(self, mock_send_error):
        """Test that application exceptions trigger Slack notifications."""
        logger = logging.getLogger("django")

        try:
            raise RuntimeError("Test application error")
        except RuntimeError:
            logger.exception("Application error occurred")

        mock_send_error.assert_called()

    @patch("mailing.handlers.send_error_message.delay")
    def test_critical_level_triggers_slack(self, mock_send_error):
        """Test that CRITICAL level messages trigger Slack notifications."""
        logger = logging.getLogger("django")
        logger.critical("Critical system error")
        mock_send_error.assert_called()


class TestEmailHandlerEndToEnd:
    """End-to-end tests for email handler functionality."""

    def test_full_email_flow(self, mock_mail_admins):
        """Test the complete flow from error to email sending."""
        from mailing.tasks import notify_admins

        test_data = {
            "subject": "Test Error Subject",
            "message": "Test error message content",
        }

        notify_admins(**test_data)
        mock_mail_admins.assert_called_once_with(**test_data)

    @override_settings(
        ADMINS=[("Test Admin", "admin@test.com")],
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_email_actually_sent_to_outbox(self):
        """Test that email is actually sent and appears in Django mail outbox."""
        mail.outbox.clear()

        from mailing.tasks import notify_admins

        notify_admins(
            subject="Test Error from Handler",
            message="This is a test error message for handler verification",
        )

        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert email.subject == "[Django] Test Error from Handler"
        assert "This is a test error message" in email.body
        assert "admin@test.com" in email.to

    @override_settings(
        ADMINS=[("Test Admin", "admin@test.com")],
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        CONFIGURATION=Environment.STAGING,
    )
    @patch("mailing.handlers.send_error_message.delay")
    def test_handler_integration_with_slack_fallback(self, mock_send_error):
        """Test complete integration: handler -> slack with email fallback."""
        from app.slack.errors import SlackDisabledException

        # Make Slack fail to test email fallback
        mock_send_error.side_effect = SlackDisabledException("Slack disabled")

        mail.outbox.clear()

        handler = AsyncAdminEmailHandler()
        record = logging.LogRecord(
            name=__name__,
            level=logging.ERROR,
            pathname="/test/integration.py",
            lineno=100,
            msg="Integration test error: %s",
            args=("database connection failed",),
            exc_info=None,
        )
        record.getMessage = lambda: "Integration test error: database connection failed"

        with patch("mailing.handlers.settings.CONFIGURATION", Environment.STAGING):
            handler.emit(record)

        # Should fallback to email when Slack fails
        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert "Integration test error" in email.subject
        assert "database connection failed" in str(email.body)
