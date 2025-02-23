import tempfile

from .config import Environment
from .development import *  # type: ignore

MEDIA_ROOT = tempfile.mkdtemp()
CONFIGURATION = Environment.TEST

CELERY_TASK_ALWAYS_EAGER = True
CELERY_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
