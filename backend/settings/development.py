from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "*hnsl_ifoyr)sj@)vp*yrdnu!k!2&%onnx3ms(wi_a&((z_gov"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]


COMPRESS_ENABLED = False


EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


INSTALLED_APPS = INSTALLED_APPS + [
    "debug_toolbar",
]


MIDDLEWARE = MIDDLEWARE + [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]


INTERNAL_IPS = ("127.0.0.1", "172.17.0.1")


# CACHES = {
#     "default": {
#         "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
#         "LOCATION": "unique-snowflake",
#     }
# }

SELECT2_CACHE_BACKEND = "default"


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
except Exception as e:
    print(f"Error while importing local settings: {e}")

MEDIA_ROOT = os.path.join(BASE_DIR, "public", "media")
