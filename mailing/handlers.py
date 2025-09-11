from django.utils.log import AdminEmailHandler


class AsyncAdminEmailHandler(AdminEmailHandler):
    """Custom AdminEmailHandler that sends emails via Celery."""

    def emit(self, record):
        """
        Emit a log record by sending it via Celery task.

        This method processes the log record and sends it to admins
        using the notify_admins Celery task instead of sending
        the email synchronously.
        """
        try:
            logger_name = record.name  # This gets the logger name
            subject = self.format_subject(f"[{logger_name}] {record.getMessage()}")
            message = self.format(record)
            self.send_mail(subject, message)
        except Exception:
            self.handleError(record)

    def send_mail(self, subject, message, *args, **kwargs):
        from mailing.tasks import notify_admins

        return notify_admins.delay(subject=subject, message=message)
