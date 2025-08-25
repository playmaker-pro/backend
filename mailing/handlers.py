from django.utils.log import AdminEmailHandler


class AsyncAdminEmailHandler(AdminEmailHandler):
    """Custom AdminEmailHandler that sends emails via Celery."""

    def emit(self, record):
        from mailing.tasks import notify_admins

        try:
            subject = self.format(record)
            if "Traceback (most recent call last)" in subject:
                subject = subject.split("Traceback (most recent call last)")[0].strip()
            else:
                subject = subject.strip()[:255]

            message = str(record.__dict__)
            notify_admins.delay(subject=subject, message=message)  # Wywołaj Celery task
        except Exception:
            self.handleError(record)  # W razie błędu logujemy go standardowo
