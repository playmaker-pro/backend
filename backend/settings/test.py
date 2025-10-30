from .config import Environment
from .development import *  # type: ignore

CONFIGURATION = Environment.TEST
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

MEDIA_ROOT = os.path.join(BASE_DIR, "media")

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
DISABLE_EXTERNAL_TASKS = True

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
