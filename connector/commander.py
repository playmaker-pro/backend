import django
from django.conf import settings

from .service import HttpService, JsonService


class Manager:
    def __init__(self, command: str, *args, **kwargs):
        django.setup()
        self.service = HttpService() if settings.SCRAPPER else JsonService()
        getattr(self, command)(args, kwargs)

    def run_action(self, action, *args, **kwargs) -> None:
        action.Command(self.service, *args, **kwargs)

    def import_scrapper_objects(self, *args, **kwargs) -> None:
        from .scripts import import_scrapper_objects

        self.run_action(import_scrapper_objects, *args, **kwargs)

    def restore_database(self, *args, **kwargs) -> None:
        from .scripts import restore_database

        self.run_action(restore_database, *args, **kwargs)

    def fix_new_structure(self, *args, **kwargs):
        from .scripts import fix_new_structure

        self.run_action(fix_new_structure, *args, **kwargs)

    def compose_urls(self, *args, **kwargs):
        from .scripts import compose_urls

        self.run_action(compose_urls, *args, **kwargs)
