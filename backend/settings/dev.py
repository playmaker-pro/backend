from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '*hnsl_ifoyr)sj@)vp*yrdnu!k!2&%onnx3ms(wi_a&((z_gov'

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ['*'] 
COMPRESS_ENABLED = True
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

INSTALLED_APPS = INSTALLED_APPS + [
    'debug_toolbar',
]

MIDDLEWARE = MIDDLEWARE + [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

INTERNAL_IPS = ("127.0.0.1", "172.17.0.1")

try:
    from .local import *
    print('loaded local settings. from local.py')
except ImportError:
    pass
