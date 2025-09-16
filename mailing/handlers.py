from django.conf import settings
from django.utils.log import AdminEmailHandler
from slack_sdk.errors import SlackApiError

from app.slack.client import send_error_message
from app.slack.errors import SlackDisabledException
from backend.settings.config import Environment


class AsyncAdminEmailHandler(AdminEmailHandler):
    """Custom AdminEmailHandler that sends emails via Celery."""

    def emit(self, record):
        """
        Emit a log record by sending it via Celery task.

        This method processes the log record and sends it to admins
        using the notify_admins Celery task instead of sending
        the email synchronously.
        """
        if settings.CONFIGURATION in [Environment.STAGING, Environment.PRODUCTION]:
            try:
                logger_name = record.name  # This gets the logger name
                subject = self.format_subject(
                    f"[{settings.CONFIGURATION}][{logger_name}] {record.getMessage()}"
                )
                message = self.format(record)
                send_error_message.delay(subject, message)
            except (SlackApiError, SlackDisabledException):
                try:
                    self.send_mail(subject, message)
                except Exception:
                    pass

    def send_mail(self, subject, message, *args, **kwargs):
        from mailing.tasks import notify_admins

        return notify_admins.delay(subject=subject, message=message)
