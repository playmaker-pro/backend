from django.core.management.base import BaseCommand
from plays.views import LeagueHistoryRefreshManager


class Command(BaseCommand):
    help = "Refresh League History data for all of leagues."
    update_handler = LeagueHistoryRefreshManager

    @property
    def allowed_keynames(self):
        return self.update_handler.service.allowed_keynames

    def add_arguments(self, parser):
        parser.add_argument("-i", "--id", type=int, default=None)
        parser.add_argument(
            "-k",
            "--keyname",
            type=str,
            default=None,
            help=f"Allowed keynames={self.allowed_keynames}",
        )

    def handle(self, *args, **options):
        _id = options.get("id")
        keyname = options.get("keyname")
        if _id:
            ids = [_id]
        else:
            ids = None

        self.stdout.write(self.style.SUCCESS(f"Parameters: {ids}, {keyname}"))
        print("--------------------")
        self.update_handler.run(verbose=True, ids=ids, keyname=keyname)
