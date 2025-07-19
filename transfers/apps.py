from django.apps import AppConfig


class TransfersConfig(AppConfig):
    name = "transfers"

    def ready(self):
        from transfers import signals
