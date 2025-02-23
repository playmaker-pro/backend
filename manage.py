#!/usr/bin/env python
import os
import sys

from backend.settings import cfg

if __name__ == "__main__":
    environment = cfg.environment

    if not environment:
        raise ValueError("Environment not set")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"backend.settings.{environment}")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
