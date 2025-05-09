from django.conf import settings
from django.core.management import BaseCommand
from django.utils import autoreload

from backend import celery_app
from backend.settings.config import Environment


class Command(BaseCommand):
    help = """Starts a Celery worker process. Reloads worker on code changes.
    This command is for celery tasks development purposes to watch celery logs.
    If you don't need console access to celery logs, you can run celery directly
    from 'runserver' command, using --celery flag like this: 'python manage.py runserver --celery'."""

    def restart_celery_worker(self) -> None:
        """
        Kill celery worker process if it's running and start a new one.

        """
        self._kill_celery_worker()
        self._start_celery_worker()

    def _kill_celery_worker(self) -> None:
        """
        Shutdown celery worker process.
        """
        celery_app.control.broadcast("shutdown")

    def _start_celery_worker(self) -> None:
        """Start celery worker process."""
        worker_args = [
            "worker",
            "--autoscale=0,4",
            "--without-mingle",
            "--without-gossip",
        ]

        if (
            settings.CONFIGURATION == Environment.DEV.value
        ):  # celery beat can be used only in dev env
            worker_args.extend(
                [
                    "--beat",
                    "--scheduler",
                    "django",
                ]
            )

        celery_app.worker_main(argv=worker_args)

    def handle(self, *args, **options):
        autoreload.run_with_reloader(self.restart_celery_worker)
