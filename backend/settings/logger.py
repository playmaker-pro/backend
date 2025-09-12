import logging.config
import os
from os.path import join
from typing import Any, Dict


def get_logging_structure(logfile_root: str) -> Dict[str, Any]:
    """
    Zwraca konfigurację loggingu dla aplikacji Django.

    Args:
        logfile_root (str): Ścieżka do katalogu z plikami logów

    Returns:
        dict: Konfiguracja loggingu w formacie dictConfig
    """
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "skip_404": {
                "()": "django.utils.log.CallbackFilter",
                "callback": lambda record: not (
                    getattr(record, "status_code", None) == 404
                    or "Broken link" in record.getMessage()
                    or "Not Found" in record.getMessage()
                ),
            },
        },
        "formatters": {
            "verbose": {
                "format": "[%(asctime)s] %(levelname)s [%(pathname)s:%(lineno)s] %(message)s",
                "datefmt": "%d/%b/%Y %H:%M:%S",
            },
            "simple": {"format": "%(levelname)s %(message)s"},
            "celery": {
                "format": "[%(asctime)s: %(levelname)s/%(name)s] %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "mail_admins": {
                "level": "ERROR",
                "class": "mailing.handlers.AsyncAdminEmailHandler",
                "filters": ["skip_404"],
            },
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "simple",
            },
            "profiles_file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": join(logfile_root, "profiles.log"),
                "formatter": "verbose",
            },
            "outbox_file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": join(logfile_root, "outbox.log"),
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
            "user_activity_file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": join(logfile_root, "user_activity.log"),
                "formatter": "verbose",
            },
            "inquiries_file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": join(logfile_root, "inquiries.log"),
                "formatter": "verbose",
            },
            "mailing_file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": join(logfile_root, "mailing.log"),
                "formatter": "verbose",
            },
            "commands_file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": join(logfile_root, "commands.log"),
                "formatter": "verbose",
            },
            "payments_file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": join(logfile_root, "payments.log"),
                "formatter": "verbose",
            },
            "celery_file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": join(logfile_root, "celery.log"),
                "formatter": "celery",
            },
        },
        "loggers": {
            "profiles": {
                "handlers": ["profiles_file"],
                "level": "DEBUG",
                "propagate": True,
            },
            "django": {
                "handlers": ["django_log_file", "console", "mail_admins"],
                "propagate": True,
                "level": "ERROR",
            },
            "django.request": {
                "handlers": ["django_log_file", "console", "mail_admins"],
                "level": "DEBUG",
                "propagate": False,
            },
            "django.db.backends": {
                "handlers": ["django_log_file", "console", "mail_admins"],
                "level": "WARNING",
                "propagate": False,
            },
            "adapters": {
                "handlers": [
                    "adapters",
                ],
                "level": "ERROR",
                "propagate": True,
            },
            "project": {
                "handlers": ["proj_log_file"],
                "level": "DEBUG",
                "propagate": True,
            },
            "route_updater": {
                "handlers": [
                    "route_updater",
                ],
                "level": "DEBUG",
                "propagate": True,
            },
            "user_activity": {
                "handlers": ["user_activity_file"],
                "level": "DEBUG",
                "propagate": True,
            },
            "inquiries": {
                "handlers": ["inquiries_file"],
                "level": "DEBUG",
                "propagate": True,
            },
            "mailing": {
                "handlers": ["mailing_file"],
                "level": "DEBUG",
                "propagate": True,
            },
            "commands": {
                "handlers": ["commands_file"],
                "level": "DEBUG",
                "propagate": True,
            },
            "payments": {
                "handlers": ["payments_file"],
                "level": "DEBUG",
                "propagate": True,
            },
            "celery": {
                "handlers": ["celery_file", "console", "mail_admins"],
                "level": "DEBUG",
                "propagate": True,
            },
            "celery.utils.functional": {
                "handlers": [],
                "level": "DEBUG",
                "propagate": False,
            },
            "celery.beat": {
                "handlers": ["console"],
                "level": "DEBUG",
                "propagate": False,
            },
            "django_celery_beat": {
                "handlers": ["celery_file", "console", "mail_admins"],
                "level": "DEBUG",
                "propagate": False,
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console", "mail_admins"],
        },
    }


def setup_logging(logfile_root: str = "_logs") -> Dict[str, Any]:
    """
    Konfiguruje logging dla aplikacji.

    Args:
        logfile_root (str): Ścieżka do katalogu z plikami logów
    """

    os.makedirs(logfile_root, exist_ok=True)

    logging_config = get_logging_structure(logfile_root)
    logging.config.dictConfig(logging_config)
    return logging_config
