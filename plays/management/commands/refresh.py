from django.core.management.base import BaseCommand
from plays.views import RefreshManager


class Command(BaseCommand):
    help = "Refresh League History data for all of leagues."

    def add_arguments(self, parser):
        parser.add_argument("-i", "--id", type=int, default=None)
        parser.add_argument("-k", "--keyname", type=str, default=None)

    def handle(self, *args, **options):
        _id = options.get("id")
        keyname = options.get("keyname")
        RefreshManager.run(verbose=True, ids=[_id], keyname=keyname)
