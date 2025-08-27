import logging

from celery import shared_task

from mailing.schemas import EmailTemplateRegistry
from mailing.services import MailingService
from profiles.models import PlayerProfile
from transfers.models import ProfileTransferRequest
from utils.cache import (
    TRANSFER_REQUEST_CACHE_KEY,
    TRANSFER_STATUS_CACHE_KEY,
    clear_cache_for_key,
)

logger = logging.getLogger("celery")


@shared_task
def clear_cache_for_transfer_requests():
    """Clear cache for transfer requests."""
    clear_cache_for_key(TRANSFER_REQUEST_CACHE_KEY)


@shared_task
def clear_cache_for_transfer_status():
    """Clear cache for transfer status."""
    clear_cache_for_key(TRANSFER_STATUS_CACHE_KEY)


@shared_task
def notify_players_about_new_transfer_request(
    transfer_request_id: int,
):  # ASK: Wszyscy piłkarze czy w określonej odległości od klubu?
    try:
        ProfileTransferRequest.objects.get(pk=transfer_request_id)
    except ProfileTransferRequest.DoesNotExist:
        logger.error(
            f"TransferRequest with id {transfer_request_id} does not exist. Unable to notify players."
        )
        return

    mail_schema = EmailTemplateRegistry.NEW_TRANSFER_REQUEST()

    for user in PlayerProfile.objects.filter(user__declared_role="P").select_related(
        "user"
    ):
        MailingService(mail_schema).send_mail(user)
