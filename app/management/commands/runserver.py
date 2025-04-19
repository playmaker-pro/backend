import subprocess

from django.core.management.commands.runserver import Command as RunServerCommand
from termcolor import colored

from backend import celery_app


class Command(RunServerCommand):
    def add_arguments(self, parser):
        parser.add_argument("--celery", action="store_true", help="Start Celery worker")
        super().add_arguments(parser)

    def inner_run(self, *args, **options):
        """
        Override inner_run method to start Celery worker if it's not running.
        Flag --celery is used to start Celery worker from runserver command.

        - Note1: that this is only for development purposes.
        - Note2: you won't see Celery logs in console if you start Celery worker this way.
                 You may want to run celery command directly: 'python manage.py celery'.
        """
        if celery_app.control.inspect().active() is None:
            if options["celery"]:
                subprocess.Popen(
                    ["python", "manage.py", "celery"],
                    stdout=subprocess.DEVNULL,  # Ukryj logi
                    stderr=subprocess.DEVNULL,  # Ukryj błędy
                )
            else:
                print(
                    colored(
                        "Celery worker is not running. To start it, run 'python manage.py celery' "
                        "if you want to see logs. You may also run 'python manage.py runserver --celery' "
                        "to start Celery worker in background.",
                        "red",
                    )
                )

        super().inner_run(*args, **options)
