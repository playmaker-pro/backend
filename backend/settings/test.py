from .dev import *

CONFIGURATION = "test"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": f"{BASE_DIR}/db.test.sqlite3",
    }
}
