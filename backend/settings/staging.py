from .base import *  # noqa
import os


DEBUG = False

BASE_URL = "https://staging.playmakerpro.usermd.net"

COMPRESS_ENABLED = True
MANAGERS = [
    ("Rafal", "rafal.kesik@gmail.com"),
    ("Jacek", "jjasinski.playmaker@gmail.com"),
]

MIDDLEWARE = ["django.middleware.common.BrokenLinkEmailsMiddleware"] + MIDDLEWARE

STATIC_ROOT = os.path.join(BASE_DIR, "public", "static")


MEDIA_ROOT = os.path.join(BASE_DIR, "public", "media")

try:
    from .local import *

    print("::> Loading custom local settings (local.py)")
except ImportError as e:
    print(f"[error] Cannot load local settings. Reason={e}")
