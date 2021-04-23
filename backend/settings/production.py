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
    import yaml
    with open('seo.yaml') as f:
        SEO_DATA = yaml.load(f, Loader=yaml.FullLoader)
except Exception as e:
    print(f'Loading seo.yaml: Not possible to write SEO_DATA due to: {e}')
    SEO_DATA = {}

try:
    from .local import *
    print(':: Loading custom local settings.')
except ImportError:
    pass
