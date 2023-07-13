from .dev import *  # type: ignore
from .config import Configuration

CONFIGURATION = Configuration.TEST
LOGGING, logger = CONFIGURATION.logger
