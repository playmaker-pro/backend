from .base import *  # noqa

DEBUG = False

BASE_URL = "https://be.playmaker.pro"


COMPRESS_ENABLED = True


ADMINS = MANAGERS = [
    ("Jakub", "jakub@bartnyk.pl"),
    ("Biuro", "biuro@playmaker.pro"),
]


COMPRESS_OFFLINE = True


STATIC_ROOT = os.path.join(BASE_DIR, "public", "static")


MEDIA_ROOT = os.path.join(BASE_DIR, "public", "media")


try:
    from .local import *
except Exception as e:
    print(f"Error while importing local settings: {e}")
