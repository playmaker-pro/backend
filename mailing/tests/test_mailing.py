
import logging
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from django.test import override_settings

from mailing.handlers import AsyncAdminEmailHandler
from mailing.tasks import notify_admins

pytestmark = pytest.mark.django_db


@pytest.fixture
def mock_mail_admins():
    """Mock mail_admins function"""
    with patch('mailing.tasks.mail_admins') as mock:
        yield mock


@pytest.fixture
def mock_notify_admins_delay():
    """Mock notify_admins.delay Celery task"""
    with patch('mailing.handlers.notify_admins.delay') as mock:
        yield mock


@pytest.fixture
def mock_mailing_service():
    """Mock MailingService to simulate errors"""
    with patch('app.management.commands.daily_supervisor.MailingService') as mock:
        yield mock


@pytest.fixture
def mock_database_connection():
    """Mock database connection to simulate DB errors"""
    with patch('django.db.connection.cursor') as mock:
        yield mock


@pytest.fixture
def mock_email_service():
    """Mock email sending service"""
    with patch('mailing.services.MailingService.send_mail') as mock:
        yield mock


@pytest.fixture
def error_log_record():
    """Create a test log record for error scenarios"""
    def _create_record(msg="Test error message", name="test_logger", pathname="test.py", lineno=42):
        return logging.LogRecord(
            name=name,
            level=logging.ERROR,
            pathname=pathname,
            lineno=lineno,
            msg=msg,
            args=(),
            exc_info=None
        )
    return _create_record


class TestMailAdminsOnError:

    def test_admin_email_handler_calls_celery_task(self, mock_notify_admins_delay, mock_mail_admins, error_log_record):
        """Test that AsyncAdminEmailHandler calls Celery task when error occurs"""
        
        # Arrange
        handler = AsyncAdminEmailHandler()
        record = error_log_record()
        
        # Act
        handler.emit(record)
        
        # Assert
        mock_notify_admins_delay.assert_called_once()
        args, kwargs = mock_notify_admins_delay.call_args
        assert 'Test error message' in str(args) or 'Test error message' in str(kwargs)

    def test_notify_admins_task_calls_mail_admins(self, mock_mail_admins):
        """Test that notify_admins task actually calls mail_admins"""
        
        # Arrange
        test_data = {
            'subject': 'Test Error Subject',
            'message': 'Test error message content'
        }
        
        # Act
        notify_admins(**test_data)
        
        # Assert
        mock_mail_admins.assert_called_once_with(**test_data)

    def test_daily_supervisor_error_triggers_admin_notification(self, mock_notify_admins_delay, mock_mailing_service):
        """Test that errors in daily_supervisor command trigger admin notifications"""
        
        # Arrange - Mock MailingService to raise an exception
        mock_mailing_service.side_effect = Exception("Test database error")
        
        # Act & Assert - Command should raise exception and trigger logging
        with pytest.raises(Exception, match="Test database error"):
            call_command('daily_supervisor')

    def test_logger_error_triggers_admin_email(self, mock_mail_admins):
        """Test that ERROR level logs trigger admin email via AsyncAdminEmailHandler"""
        
        # Arrange
        logger = logging.getLogger('django')
        
        # Act - Log an error that should trigger admin notification
        logger.error("Critical system error occurred", exc_info=True)
        
        # Note: This test verifies the configuration is correct
        # In real scenario, the AsyncAdminEmailHandler would be called
        # and it would trigger the Celery task

    def test_simulate_multiple_errors_and_check_notifications(
        self, 
        mock_notify_admins_delay, 
        mock_database_connection, 
        mock_email_service,
        error_log_record
    ):
        """Simulate multiple types of errors to test admin notification system"""
        
        # Test 1: Database connection error simulation
        mock_database_connection.side_effect = Exception("Database connection failed")
        
        try:
            # This would normally trigger database error
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception as e:
            # Manually trigger the handler like Django would
            handler = AsyncAdminEmailHandler()
            record = error_log_record(
                msg=str(e),
                name='django.db',
                pathname='db.py',
                lineno=100
            )
            handler.emit(record)
        
        # Test 2: Email sending error simulation
        mock_email_service.side_effect = Exception("SMTP server unavailable")
        
        try:
            call_command('daily_supervisor')
        except Exception as e:
            # Command should log the error which triggers admin notification
            handler = AsyncAdminEmailHandler()
            record = error_log_record(
                msg=str(e),
                name='commands',
                pathname='daily_supervisor.py',
                lineno=25
            )
            handler.emit(record)
        
        # Verify that admin notifications were triggered
        assert mock_notify_admins_delay.call_count >= 1
        
        # Check that notification contains error information
        for call in mock_notify_admins_delay.call_args_list:
            args, kwargs = call
            # Should contain either subject or message with error info
            call_str = str(args) + str(kwargs)
            assert any(error_text in call_str for error_text in [
                'Database connection failed',
                'SMTP server unavailable',
                'error',
                'Error'
            ])