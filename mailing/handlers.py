from django.utils.log import AdminEmailHandler

from mailing.tasks import notify_admins


class AsyncAdminEmailHandler(AdminEmailHandler):
    """Custom AdminEmailHandler that sends emails via Celery."""

    def emit(self, record):
        try:
            subject = self.format(record)
            message = str(record.__dict__)
            notify_admins.delay(subject, message)  # Wywołaj Celery task
        except Exception:
            self.handleError(record)  # W razie błędu logujemy go standardowo
