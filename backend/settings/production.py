from .base import *  # noqa

DEBUG = False

BASE_URL = "https://be.playmaker.pro"

COMPRESS_ENABLED = True

ADMINS = MANAGERS = [
    ("Jakub", "jakub@playmaker.pro"),
    ("Biuro", "biuro@playmaker.pro"),
    ("Bartosz", "bartosz@playmaker.pro"),
]

COMPRESS_OFFLINE = True

STATIC_ROOT = os.path.join(BASE_DIR, "public", "static")
MEDIA_ROOT = os.path.join(BASE_DIR, "public", "media")


try:
    from .local import *
except Exception as e:
    print(f"Error while importing local settings: {e}")
