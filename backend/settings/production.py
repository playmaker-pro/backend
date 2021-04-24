from .base import *  # noqa

import os

DEBUG = False

BASE_URL = 'https://playmaker.pro'

COMPRESS_ENABLED = True
MANAGERS = [
    ('Rafal', 'rafal.kesik@gmail.com'), 
    ('Jacek', 'jjasinski.playmaker@gmail.com')]


ADMINS = MANAGERS

COMPRESS_OFFLINE = True

STATIC_ROOT = os.path.join(BASE_DIR, 'public', 'static')

MEDIA_ROOT = os.path.join(BASE_DIR, 'public', 'media')

try:
    from .local import *
    print(':: Loading custom local settings.')
except ImportError:
    pass
