import logging
from unittest.mock import patch

import pytest
from django.core import mail
from django.test import TestCase, override_settings

from mailing.handlers import AsyncAdminEmailHandler


@pytest.fixture
def mock_notify_admins():
    """Mock for notify_admins Celery task."""
    with patch("mailing.tasks.notify_admins.delay") as mock:
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
            exc_info=True,
        )
        record.getMessage = lambda: "Error with exception"
        return record


class TestAsyncAdminEmailHandler:
    """Test cases for AsyncAdminEmailHandler."""

    def setup_method(self):
        """Setup for each test method."""
        self.handler = AsyncAdminEmailHandler()
        self.handler.setLevel(logging.ERROR)

    def test_handler_initialization(self):
        """Test that handler initializes correctly."""
        assert isinstance(self.handler, AsyncAdminEmailHandler)
        assert self.handler.level == logging.ERROR

    def test_emit_calls_celery_task(self, mock_notify_admins, error_log_record):
        """Test that emit method calls Celery task with correct parameters."""
        self.handler.emit(error_log_record)

        mock_notify_admins.assert_called_once()
        call_args = mock_notify_admins.call_args[1]
        assert "Test error message" in str(call_args)

    def test_emit_with_exception_info(self, mock_notify_admins, exception_log_record):
        """Test emit with exception information."""
        self.handler.emit(exception_log_record)
        mock_notify_admins.assert_called_once()

    def test_emit_handles_celery_task_exception(
        self, mock_notify_admins, error_log_record
    ):
        """Test that handler gracefully handles Celery task failures."""
        mock_notify_admins.side_effect = Exception("Celery task failed")

        with patch.object(self.handler, "handleError") as mock_handle_error:
            self.handler.emit(error_log_record)
            mock_handle_error.assert_called_once_with(error_log_record)

    def test_emit_warning_level_not_sent(self, mock_notify_admins):
        """Test that WARNING level messages are not sent to admins."""
        self.handler.setLevel(logging.WARNING)

        record = logging.LogRecord(
            name="test_logger",
            level=logging.WARNING,
            pathname="/test/path.py",
            lineno=42,
            msg="Warning message",
            args=(),
            exc_info=None,
        )
        record.getMessage = lambda: "Warning message"

        self.handler.emit(record)

    def test_format_and_message_content(self, mock_notify_admins):
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

        mock_notify_admins.assert_called_once()
        call_args = mock_notify_admins.call_args[1]
        assert "critical issue" in str(call_args)


@override_settings(ADMINS=[("Test Admin", "admin@test.com")])
class TestAsyncAdminEmailHandlerIntegration(TestCase):
    """Integration tests for AsyncAdminEmailHandler with Django logging."""

    def test_django_logger_error_triggers_email(self):
        """Test that Django logger errors trigger email notifications."""
        with patch("mailing.tasks.notify_admins.delay") as mock_notify_admins:
            logger = logging.getLogger("django")
            logger.error("Test Django error for email notification")
            mock_notify_admins.assert_called()

    def test_application_exception_triggers_email(self):
        """Test that application exceptions trigger email notifications."""
        with patch("mailing.tasks.notify_admins.delay") as mock_notify_admins:
            logger = logging.getLogger("django")

            try:
                raise RuntimeError("Test application error")
            except RuntimeError:
                logger.exception("Application error occurred")

            mock_notify_admins.assert_called()

    def test_critical_level_triggers_email(self):
        """Test that CRITICAL level messages trigger email notifications."""
        with patch("mailing.tasks.notify_admins.delay") as mock_notify_admins:
            logger = logging.getLogger("django")
            logger.critical("Critical system error")
            mock_notify_admins.assert_called()


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
        assert email.subject == "Test Error from Handler"
        assert "This is a test error message" in email.body
        assert "admin@test.com" in email.to

    @override_settings(
        ADMINS=[("Test Admin", "admin@test.com")],
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_handler_integration_with_outbox(self):
        """Test complete integration: handler -> task -> email outbox."""
        mail.outbox.clear()

        handler = AsyncAdminEmailHandler()
        record = logging.LogRecord(
            name="django",
            level=logging.ERROR,
            pathname="/test/integration.py",
            lineno=100,
            msg="Integration test error: %s",
            args=("database connection failed",),
            exc_info=None,
        )
        record.getMessage = lambda: "Integration test error: database connection failed"

        handler.emit(record)

        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert "Integration test error" in email.subject
        assert "database connection failed" in str(email.body)
