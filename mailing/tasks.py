import logging

from celery import shared_task
from django.core.mail import mail_admins, send_mail

from mailing.schemas import Envelope

logger: logging.Logger = logging.getLogger("mailing")


@shared_task
def notify_admins(subject, message):
    mail_admins(subject, message)


@shared_task
def send(
    data: dict,  # Envelope.model_dump()
):
    """
    Send an email to the specified recipients.
    """
    envelope = Envelope.model_validate(data)
    try:
        send_mail(
            **envelope.mail.data,
            recipient_list=envelope.recipients,
        )
    except Exception as err:
        logger.error(
            f"subject={envelope.mail.subject}, recipients={envelope.recipients}, error={str(err)}"
        )
    else:
        logger.info(
            f"subject={envelope.mail.subject}, recipients={envelope.recipients}"
        )


@shared_task
def send_many(recipients: list, data: dict):
    """
    Send an email to multiple recipients.
    """
    for recipient in recipients:
        envelope = Envelope.model_validate(mail=data, recipients=[recipient])
        send.delay(envelope.model_dump())
