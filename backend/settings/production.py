from .base import *  # noqa

DEBUG = False

DOMAIN_ADDRESS = 'http://suumyx.usermd.net'


try:
    from .local import *
    print(':: Loading custom local settings.')
except ImportError:
    pass
