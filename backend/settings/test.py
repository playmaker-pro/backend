import tempfile

from .dev import *  # type: ignore

CONFIGURATION = Environment.TEST
MEDIA_ROOT = tempfile.mkdtemp()
