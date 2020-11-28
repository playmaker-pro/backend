import logging


def silence_explamation_mark():
    logger = logging.getLogger('django.db.backends.schema')
    logger.propagate = False
