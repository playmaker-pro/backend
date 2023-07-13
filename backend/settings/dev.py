from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
CONFIGURATION = Configuration.DEV

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


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

SELECT2_CACHE_BACKEND = "default"


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}

try:
    from .local import *

    print("::> Loading custom local settings (local.py)")
except ImportError as e:
    print(f"[error] Cannot load local settings. Reason={e}")

LOGGING, logger = CONFIGURATION.logger
