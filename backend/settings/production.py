from .base import *  # noqa

DEBUG = False

BASE_URL = 'http://suumyx.usermd.net'


try:
    from .local import *
    print(':: Loading custom local settings.')
except ImportError:
    pass
