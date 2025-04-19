from celery import shared_task
from django.core.cache import cache


@shared_task
def reload_cache_for_transfer_request(*args, **kwargs):
    """
    Reload the cache for a transfer request.
    """
    cache.delete_pattern("*transfer-requests*")
