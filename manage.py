#!/usr/bin/env python
import os
import sys

from backend.settings.environment import Environment

if __name__ == "__main__":
    config = Environment.DEV

    try:
        from backend.settings import local

        config = local.CONFIGURATION
        print(f":: loading {config} configuration")
    except:
        pass

    assert config
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"backend.settings.{config}")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
