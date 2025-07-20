from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from transfers.models import ProfileTransferRequest, ProfileTransferStatus
from transfers.tasks import (
    clear_cache_for_transfer_requests,
    clear_cache_for_transfer_status,
)


@receiver(post_save, sender=ProfileTransferRequest)
def profile_transfer_request_post_save(sender, instance, created, **kwargs):
    clear_cache_for_transfer_requests.delay()


@receiver(post_delete, sender=ProfileTransferRequest)
def profile_transfer_request_post_delete(sender, instance, **kwargs):
    clear_cache_for_transfer_requests.delay()


@receiver(post_save, sender=ProfileTransferStatus)
def profile_transfer_status_post_save(sender, instance, created, **kwargs):
    clear_cache_for_transfer_status.delay()


@receiver(post_delete, sender=ProfileTransferStatus)
def profile_transfer_status_post_delete(sender, instance, **kwargs):
    clear_cache_for_transfer_status.delay()
