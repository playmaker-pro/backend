from .base import *

DEBUG = True
SECRET_KEY = "*hnsl_ifoyr)sj@)vp*yrdnu!k!2&%onnx3ms(wi_a&((z_gov"
ALLOWED_HOSTS = ["*"]
COMPRESS_ENABLED = False


EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INTERNAL_IPS = ("127.0.0.1", "172.17.0.1")

SELECT2_CACHE_BACKEND = "default"

try:
    from .local import *
except Exception as e:
    print(f"Error while importing local settings: {e}")

MEDIA_ROOT = os.path.join(BASE_DIR, "public", "media")
