from .base import *  # noqa

DEBUG = False

DOMAIN_ADDRESS = 'https://staging.playmakerpro.usermd.net'


MANAGERS = [('Rafal', 'rafal.kesik@gmail.com'), ('Jacek', 'jjasinski.playmaker@gmail.com')]


try:
    from .local import *  # noqa
    print(':: Loading custom local settings.')
except ImportError:
    pass
