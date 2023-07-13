import enum
from .logger import get_base_logging_structure, get_dev_logging_structure
import logging

LOGGING_ROOT = "_logs"


class Configuration(enum.Enum):
    PRODUCTION: str = "production"
    STAGING: str = "staging"
    DEV: str = "dev"
    TEST: str = "test"

    @property
    def logging_structure(self) -> dict:
        """Get logging structure for proper environment"""
        if self.value == self.PRODUCTION.value:
            return get_base_logging_structure(LOGGING_ROOT)
        else:
            return get_dev_logging_structure(LOGGING_ROOT)

    @property
    def logger(self) -> (dict, logging.Logger):
        """
        Get logger for given environment
        Reset logging
        (see http://www.caktusgroup.com/blog/2015/01/27/Django-Logging-Configuration-logging_config-default-settings-logger/)
        """
        import logging.config

        structure = self.logging_structure
        logging.config.dictConfig(structure)
        logger = logging.getLogger(f"project.{__name__}")
        return structure, logger
