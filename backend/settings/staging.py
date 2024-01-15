import os

from .base import *  # noqa

DEBUG = False
CONFIGURATION = Environment.STAGING
BASE_URL = "https://staging.playmakerpro.usermd.net"

COMPRESS_ENABLED = True
MANAGERS = [
    ("Rafal", "rafal.kesik@gmail.com"),
    ("Jacek", "jjasinski.playmaker@gmail.com"),
]

MIDDLEWARE = ["django.middleware.common.BrokenLinkEmailsMiddleware"] + MIDDLEWARE

STATIC_ROOT = os.path.join(BASE_DIR, "public", "static")


MEDIA_ROOT = os.path.join(BASE_DIR, "public", "media")


MEMCACHED_CACHE_SOCK = None

LOGGING["handlers"]["mocker"] = {
    "level": "DEBUG",
    "class": "logging.FileHandler",
    "filename": join(LOGGING_ROOTDIR, "mocker.log"),
    "formatter": "verbose",
}
LOGGING["loggers"]["mocker"] = {
    "handlers": ["mocker", "console"],
    "level": "INFO",
}

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(f"project.{__name__}")

try:
    from .local import *

    print("::> Loading custom local settings (local.py)")
except ImportError as e:
    print(f"[error] Cannot load local settings. Reason={e}")


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": MEMCACHED_CACHE_SOCK,
    }
}
