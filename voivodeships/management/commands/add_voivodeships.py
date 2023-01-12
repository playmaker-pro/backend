from django.core.management import BaseCommand

from voivodeships.services import VoivodeshipService  # noqa


class Command(BaseCommand):
    help = "Create voivodeships"

    def handle(self, *args, **options):

        manager = VoivodeshipService()
        manager.save_to_db()
