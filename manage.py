#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    
    config = 'dev'

    try:
        from backend.settings import local
        config = local.CONFIGURATION
    except:
        pass

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"backend.settings.{config}")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
