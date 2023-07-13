# Support new str.format syntax in log messages
#
# Based on http://stackoverflow.com/a/25433007 and
# http://stackoverflow.com/a/26003573 and logging cookbook
# https://docs.python.org/3/howto/logging-cookbook.html#use-of-alternative-formatting-styles
#
# It's worth noting that this implementation has problems if key words
# used for brace substitution include level, msg, args, exc_info,
# extra or stack_info. These are argument names used by the log method
# of Logger. If you need to one of these names then modify process to
# exclude these names or just remove log_kwargs from the _log call. On
# a further note, this implementation also silently ignores misspelled
# keywords meant for the Logger (eg. ectra).
#


from os.path import join
import logging


class NewStyleLogMessage(object):
    def __init__(self, message, *args, **kwargs):
        self.message = message
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        args = (i() if callable(i) else i for i in self.args)
        kwargs = dict((k, v() if callable(v) else v) for k, v in self.kwargs.items())

        return self.message.format(*args, **kwargs)


N = NewStyleLogMessage


class StyleAdapter(logging.LoggerAdapter):
    def __init__(self, logger, extra=None):
        super(StyleAdapter, self).__init__(logger, extra or {})

    def log(self, level, msg, *args, **kwargs):
        if self.isEnabledFor(level):
            msg, log_kwargs = self.process(msg, kwargs)
            self.logger._log(level, N(msg, *args, **kwargs), (), **log_kwargs)


logger = StyleAdapter(logging.getLogger("project"))
#   Emits "Lazily formatted log entry: 123 foo" in log
# logger.debug('Lazily formatted entry: {0} {keyword}', 123, keyword='foo')


def get_base_logging_structure(logfile_root: str) -> dict:
    """Logging structure used as initial logging structure (production)"""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "[%(asctime)s] %(levelname)s [%(pathname)s:%(lineno)s] %(message)s",
                "datefmt": "%d/%b/%Y %H:%M:%S",
            },
            "simple": {"format": "%(levelname)s %(message)s"},
        },
        "handlers": {
            "profiles_file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": join(logfile_root, "profiles.log"),
                "formatter": "verbose",
            },
            "data_log_file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": join(logfile_root, "data.log"),
                "formatter": "verbose",
            },
            "django_log_file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": join(logfile_root, "django.log"),
                "formatter": "verbose",
            },
            "proj_log_file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": join(logfile_root, "project.log"),
                "formatter": "verbose",
            },
            "route_updater": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": join(logfile_root, "route.updater.log"),
                "formatter": "verbose",
            },
            "adapters": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": join(logfile_root, "adapters.log"),
                "formatter": "verbose",
            },
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "simple",
            },
        },
        "loggers": {
            "profiles": {
                "handlers": ["console", "profiles_file"],
                "level": "DEBUG",
            },
            "django": {
                "handlers": ["django_log_file"],
                "propagate": True,
                "level": "ERROR",
            },
            "adapters": {
                "handlers": ["adapters"],
                "level": "ERROR",
            },
            "project": {
                "handlers": ["proj_log_file"],
                "level": "DEBUG",
            },
            "route_updater": {
                "handlers": ["console", "route_updater"],
                "level": "DEBUG",
            },
        },
    }


def get_dev_logging_structure(LOGFILE_ROOT: str) -> dict:
    """Logging structure for development/staging"""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "[%(asctime)s] %(levelname)s [%(pathname)s:%(lineno)s] %(message)s",
                "datefmt": "%d/%b/%Y %H:%M:%S",
            },
            "simple": {"format": "%(levelname)s %(message)s"},
        },
        "handlers": {
            "profiles_file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": join(LOGFILE_ROOT, "profiles.log"),
                "formatter": "verbose",
            },
            "data_log_file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": join(LOGFILE_ROOT, "data.log"),
                "formatter": "verbose",
            },
            "django_log_file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": join(LOGFILE_ROOT, "django.log"),
                "formatter": "verbose",
            },
            "proj_log_file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": join(LOGFILE_ROOT, "project.log"),
                "formatter": "verbose",
            },
            "route_updater": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": join(LOGFILE_ROOT, "route.updater.log"),
                "formatter": "verbose",
            },
            "adapters": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": join(LOGFILE_ROOT, "adapters.log"),
                "formatter": "verbose",
            },
            "mocker": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": join(LOGFILE_ROOT, "mocker.log"),
                "formatter": "verbose",
            },
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "simple",
            },
        },
        "loggers": {
            "profiles": {
                "handlers": ["console", "profiles_file"],
                "level": "DEBUG",
            },
            "django": {
                "handlers": ["django_log_file"],
                "propagate": True,
                "level": "ERROR",
            },
            "adapters": {
                "handlers": ["adapters"],
                "level": "ERROR",
            },
            "mocker": {
                "handlers": ["mocker", "console"],
                "level": "INFO",
            },
            "project": {
                "handlers": ["proj_log_file"],
                "level": "DEBUG",
            },
            "route_updater": {
                "handlers": ["console", "route_updater"],
                "level": "DEBUG",
            },
        },
    }
