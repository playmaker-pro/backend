import logging as _logging

from django.conf import settings as _settings

from mailing.schemas import EmailType, MailContent
from mailing.services import MailingService


class EmailOnErrorHandler(_logging.Handler):
    def __init__(self):
        super().__init__()

    def emit(self, record):
        if record.levelno >= _logging.ERROR:
            try:
                context = {"body": self.format(record)}

                mail_content = MailContent(
                    subject="[SYSTEM] Payment error",
                    template_path="mailing/mails/system_error.html",
                )

                mailing_service = MailingService(
                    context=context,
                    recipients=[_settings.ADMIN_EMAIL],
                    mail_content=mail_content,
                    email_type=EmailType.SYSTEM,
                    sender=None,
                )
                mailing_service.send_mail()

            except Exception as e:
                print(f"Failed to send error email: {e}")


logger = _logging.getLogger("payments")
_email_handler = EmailOnErrorHandler()
logger.addHandler(_email_handler)
