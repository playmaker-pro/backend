import logging
import typing

from django.conf import settings
from django.core.cache import cache
from rest_framework.request import Request

from backend.settings import cfg

logger = logging.getLogger(__name__)

TRANSFER_REQUEST_CACHE_KEY = f"*{cfg.redis.key_prefix.transfer_requests}:*"
TRANSFER_STATUS_CACHE_KEY = f"*{cfg.redis.key_prefix.list_profiles}:*transfer_status=*"


class CachedResponse:
    def __init__(
        self,
        cache_key: str,
        request: Request,
        cache_timeout: int = settings.DEFAULT_CACHE_LIFESPAN,
    ):
        self._cache_key = cache_key
        self._cache_timeout = cache_timeout
        self._request = request

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb): ...

    @property
    def data(self):
        """Retrieve cached data if available."""
        return cache.get(self._cache_key)

    @data.setter
    def data(self, data: typing.Any) -> None:
        cache.set(self._cache_key, data, timeout=self._cache_timeout)


def get_cache_backend_type() -> str:
    """Get the type of cache backend being used."""
    try:
        cache_backend = settings.CACHES["default"]["BACKEND"]
        if "redis" in cache_backend.lower():
            return "redis"
        elif "locmem" in cache_backend.lower():
            return "locmem"
        elif "memcached" in cache_backend.lower():
            return "memcached"
        elif "dummy" in cache_backend.lower():
            return "dummy"
        else:
            return "unknown"
    except Exception:
        return "unknown"


def get_keys(cache_key_pattern: str) -> typing.List[str]:
    """Get keys matching the cache key pattern - works with different cache backends."""
    backend_type = get_cache_backend_type()

    try:
        if backend_type == "redis":
            # Redis backend - można użyć keys()
            from django_redis import get_redis_connection

            client = get_redis_connection("default")
            keys = client.keys(cache_key_pattern)
            return [
                key.decode("utf-8") if isinstance(key, bytes) else key for key in keys
            ]

        elif backend_type == "locmem":
            # LocMemCache - nie ma natywnego sposobu na listowanie kluczy
            # Musimy użyć wewnętrznej struktury (nie zalecane w produkcji)
            logger.warning(
                "LocMemCache doesn't support key pattern matching. Consider using Redis for better cache management."
            )
            return []

        elif backend_type == "memcached":
            # Memcached też nie wspiera listowania kluczy
            logger.warning(
                "Memcached doesn't support key pattern matching. Consider using Redis for better cache management."
            )
            return []

        else:
            logger.warning(
                f"Cache backend '{backend_type}' doesn't support key pattern matching."
            )
            return []

    except Exception as e:
        logger.error(f"Error getting keys from cache: {e}")
        return []


def clear_cache_for_key(cache_key_pattern: str) -> None:
    """Clear specific cache key - works with different cache backends."""
    backend_type = get_cache_backend_type()

    try:
        if backend_type == "redis":
            from django_redis import get_redis_connection

            client = get_redis_connection("default")
            keys = client.keys(cache_key_pattern)

            if keys:
                client.delete(*keys)
                logger.info(
                    f"Cleared {len(keys)} cache keys matching pattern '{cache_key_pattern}'."
                )
            else:
                logger.info(
                    f"No cache keys found matching pattern '{cache_key_pattern}'."
                )

        elif backend_type in ["locmem", "memcached"]:
            logger.warning(
                f"Cache backend '{backend_type}' doesn't support pattern-based deletion."
            )
            logger.info(
                "Consider using cache.clear() to clear all cache or specify exact keys."
            )

        elif backend_type == "dummy":
            # DummyCache - nic nie robi
            logger.info("DummyCache backend - no operation performed.")

        else:
            logger.warning(
                f"Unknown cache backend '{backend_type}' - cannot clear keys."
            )

    except Exception as e:
        logger.error(f"Error clearing cache: {e}")


def clear_all_cache() -> None:
    """Clear all cache entries - works with any cache backend."""
    try:
        cache.clear()
        logger.info("Cleared all cache entries.")
    except Exception as e:
        logger.error(f"Error clearing all cache: {e}")


def clear_specific_keys(keys: typing.List[str]) -> None:
    """Clear specific cache keys - works with any cache backend."""
    if not keys:
        logger.info("No keys provided to clear.")
        return

    try:
        deleted_count = 0
        for key in keys:
            cache.delete(key)
            deleted_count += 1

        logger.info(f"Cleared {deleted_count} specific cache keys.")

    except Exception as e:
        logger.error(f"Error clearing specific cache keys: {e}")
