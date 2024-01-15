from .dev import *  # type: ignore
import tempfile

CONFIGURATION = Environment.TEST
MEDIA_ROOT = tempfile.mkdtemp()
