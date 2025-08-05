import logging

from celery import shared_task
from django.core.mail import mail_admins, send_mail

logger: logging.Logger = logging.getLogger("mailing")


@shared_task
def notify_admins(**data):
    mail_admins(**data)


@shared_task
def send(**data):
    """
    Send an email to the specified recipients.
    """
    try:
        send_mail(
            **data,
        )
    except Exception as err:
        print(err)
        logger.error(
            f"subject={data['subject']}, recipients={data['recipient_list']}, error={str(err)}"
        )
    else:
        logger.info(f"subject={data['subject']}, recipients={data['recipient_list']}")
