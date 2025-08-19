import logging as _logging

from mailing.schemas import EmailTemplateRegistry, Envelope


class EmailOnErrorHandler(_logging.Handler):
    def __init__(self):
        super().__init__()

    def emit(self, record):
        if record.levelno >= _logging.ERROR:
            try:
                context = {
                    "body": self.format(record),
                    "subject": "[SYSTEM] Payment Error",
                }

                mail_content = EmailTemplateRegistry.SYSTEM_ERROR(context)
                envelope = Envelope(mail=mail_content)
                envelope.send_to_admins()

            except Exception as e:
                print(f"Failed to send error email: {e}")


logger = _logging.getLogger("payments")
_email_handler = EmailOnErrorHandler()
logger.addHandler(_email_handler)
