from .base import *  # noqa

DEBUG = False

BASE_URL = "https://staging.playmakerpro.usermd.net"

COMPRESS_ENABLED = True

ADMINS = MANAGERS = [
    ("Jakub", "jakub@playmaker.pro"),
    ("Biuro", "biuro@playmaker.pro"),
]

STATIC_ROOT = os.path.join(BASE_DIR, "public", "static")


MEDIA_ROOT = os.path.join(BASE_DIR, "public", "media")


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
