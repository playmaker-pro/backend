from django.core.management.base import BaseCommand

from profiles.models import PlayerProfile


class Command(BaseCommand):
    help = "Create relation with metrics"

    def handle(self, *args, **options):
        qs = PlayerProfile.objects.filter(playermetrics__isnull=True)
        print(f"Found {qs.count()} profiles without metrics.")

        for player in qs:
            player.ensure_playermetrics_exist()
