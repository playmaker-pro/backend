from celery import shared_task
from celery.utils.log import get_task_logger

from mailing.schemas import EmailTemplateRegistry
from mailing.services import MailingService
from mailing.utils import build_email_context
from profiles.models import PlayerProfile
from transfers.models import ProfileTransferRequest
from utils.cache import (
    TRANSFER_REQUEST_CACHE_KEY,
    TRANSFER_STATUS_CACHE_KEY,
    clear_cache_for_key,
)

logger = get_task_logger(__name__)


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
):
    try:
        ProfileTransferRequest.objects.get(pk=transfer_request_id)
    except ProfileTransferRequest.DoesNotExist:
        logger.error(
            f"TransferRequest with id {transfer_request_id} does not exist. Unable to notify players."
        )
        return

    mail_schema = EmailTemplateRegistry.NEW_CLUB_OFFER

    for player in PlayerProfile.objects.filter(user__declared_role="P").select_related(
        "user"
    ):
        context = build_email_context(player.user)
        MailingService(mail_schema(context)).send_mail(player.user)
