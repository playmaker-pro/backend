from django.apps import AppConfig


class AppConfig(AppConfig):
    name = "app"

    def ready(self):
        from app.celery.tasks import refresh_periodic_tasks

        refresh_periodic_tasks()
