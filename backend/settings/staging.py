from .base import *  # noqa
import os

DEBUG = False

BASE_URL = 'https://staging.playmakerpro.usermd.net'


MANAGERS = [('Rafal', 'rafal.kesik@gmail.com'), ('Jacek', 'jjasinski.playmaker@gmail.com')]



STATIC_ROOT = os.path.join(BASE_DIR, 'public', 'static')


MEDIA_ROOT = os.path.join(BASE_DIR, 'public', 'media')


try:
    from .local import *  # noqa
    print(':: Loading custom local settings.')
except ImportError:
    pass
