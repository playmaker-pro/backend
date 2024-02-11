import logging as _logging

from django.conf import settings as _settings

from mailing.models import EmailTemplate as _EmailTemplate
from mailing.schemas import EmailSchema as _EmailSchema


class EmailOnErrorHandler(_logging.Handler):
    def __init__(self):
        super().__init__()

    def emit(self, record):
        if record.levelno >= _logging.ERROR:
            body = self.format(record)
            schema = _EmailSchema(
                type=_EmailTemplate.EmailType.SYSTEM,
                subject="[SYSTEM] Payment error",
                body=body,
                recipients=[_settings.ADMIN_EMAIL],
            )
            _EmailTemplate.send_email(schema)


logger = _logging.getLogger("payments")
_email_handler = EmailOnErrorHandler()
logger.addHandler(_email_handler)
