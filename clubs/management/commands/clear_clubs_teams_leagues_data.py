from django.core.management.base import BaseCommand
from django.db import transaction

from clubs.models import Club, League, LeagueHistory, Team, TeamHistory


class Command(BaseCommand):
    """
    Custom management command to clear data from specific database tables.

    This command is designed to delete all records from the specified tables
    in a transactional manner. It ensures that data from the following models
    are completely removed: FollowTeam, Club, Team, TeamHistory, League, and
    LeagueHistory.

    Usage:
        python manage.py clear_clubs_teams_leagues_data
    """

    help = "Clears data from specified tables"

    def handle(self, *args, **kwargs) -> None:
        with transaction.atomic():
            # Deleting records from each table
            Club.objects.all().delete()
            Team.objects.all().delete()
            TeamHistory.objects.all().delete()
            League.objects.all().delete()
            LeagueHistory.objects.all().delete()

        # Indicate successful execution
        self.stdout.write(self.style.SUCCESS("Successfully cleared data from tables"))
