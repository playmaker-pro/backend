import os
import sys
from backend.settings.config import Configuration
from connector.commander import Manager

if __name__ == "__main__":
    config = Configuration.DEV

    try:
        from backend.settings import local

        config = local.CONFIGURATION
    except:
        pass

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"backend.settings.{config}")

    try:
        command = sys.argv[1]
    except IndexError:
        raise Exception("No command given.")

    try:
        Manager(command, sys.argv[2:])
    except IndexError:
        Manager(command)
