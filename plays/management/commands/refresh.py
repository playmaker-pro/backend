from django.core.management.base import BaseCommand
from plays.views import RefreshManager


class Command(BaseCommand):
    help = "Refresh League History data for all of leagues."

    def handle(self, *args, **options):
        RefreshManager.run()
