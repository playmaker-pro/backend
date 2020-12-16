from django.apps import AppConfig


class NotificationConfig(AppConfig):
    name = 'notifications'
    verbose_name = "User notifications"

    def ready(self):
        from . import signals  # noqa
