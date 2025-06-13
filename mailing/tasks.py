import logging as _logging
import traceback

from celery import shared_task
from django.core.mail import mail_admins, send_mail

logger: _logging.Logger = _logging.getLogger("mailing")


@shared_task
def notify_admins(subject, message):
    mail_admins(subject, message)


@shared_task
def send(log: str, **kwargs):
    """
    Send an email to the specified recipients.
    """
    try:
        send_mail(**kwargs)
    except Exception as e:
        logger.error(f"[ERROR]\n{log}\n{e}\n{traceback.format_exc()}")
    else:
        logger.info(f"[SUCCESS]\n{log}")
