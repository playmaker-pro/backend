from celery import shared_task

from utils.cache import (
    TRANSFER_REQUEST_CACHE_KEY,
    TRANSFER_STATUS_CACHE_KEY,
    clear_cache_for_key,
)


@shared_task
def clear_cache_for_transfer_requests():
    """Clear cache for transfer requests."""
    clear_cache_for_key(TRANSFER_REQUEST_CACHE_KEY)


@shared_task
def clear_cache_for_transfer_status():
    """Clear cache for transfer status."""
    clear_cache_for_key(TRANSFER_STATUS_CACHE_KEY)
