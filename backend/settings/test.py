from .config import Environment
from .development import *  # type: ignore

CONFIGURATION = Environment.TEST

from .base import MEDIA_ROOT

MEDIA_ROOT = MEDIA_ROOT

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
