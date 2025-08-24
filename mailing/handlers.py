import logging

from django.utils.log import AdminEmailHandler


class AsyncAdminEmailHandler(AdminEmailHandler):
    """Custom AdminEmailHandler that sends emails via Celery."""

    def emit(self, record):
        from mailing.tasks import notify_admins

        try:
            print(f"Handler emit called with level: {record.levelno}, ERROR: {logging.ERROR}")
            # Wywołaj original emit tylko jeśli handler spełnia warunki
            if record.levelno >= logging.ERROR:
                print("Condition met, calling notify_admins")
                subject = self.format(record)
                message = str(record.__dict__)
                notify_admins.delay(subject, message)
            else:
                print("Condition NOT met")
        except Exception as e:
            print(f"Exception in emit: {e}")
            self.handleError(record)
