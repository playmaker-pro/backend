from .base import *  # noqa

DEBUG = False

BASE_URL = 'https://playmaker.pro'


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
