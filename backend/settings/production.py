from .base import *  # noqa

DEBUG = False

try:
    from .local import *
    print(':: Loading custom local settings.')
except ImportError:
    pass
