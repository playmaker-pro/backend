from django.apps import AppConfig


class ExternalLinksConfig(AppConfig):
    name = "external_links"

    def ready(self):
        from . import signals  # noqa
