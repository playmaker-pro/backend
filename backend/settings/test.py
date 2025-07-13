import tempfile

from backend.settings.config import Environment

from .development import *  # type: ignore

MEDIA_ROOT = tempfile.mkdtemp()
CONFIGURATION = Environment.TEST

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
