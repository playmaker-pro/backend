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

try:
    from .local import *
except Exception as e:
    print(f"Error while importing local settings: {e}")
