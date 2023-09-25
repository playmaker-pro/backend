from django.core.management.base import BaseCommand
from django.db import transaction

from clubs.management.commands.utils import generate_club_or_team_short_name
from clubs.models import Club, Team


class Command(BaseCommand):
    """
    A custom management command that generates short names for clubs and teams.

    This command iterates over all clubs in the database, generates a short name
    for each club, and then does the same for each team associated with that club.
    The generated names are saved directly to the database.
    """

    help = "Create short names for club and team based on their name"

    def handle(self, *args, **kwargs):
        """
        The main logic of the command. It processes each club and its associated teams
        to generate and save short names. The results are then printed to the standard
        output.
        """
        total_clubs = Club.objects.count()
        processed_clubs = 0
        with transaction.atomic():
            for club in Club.objects.all():
                club.short_name = generate_club_or_team_short_name(club)
                club.save()

                # Get all teams associated with the current club and process them
                for team in Team.objects.filter(club=club):
                    team.short_name = generate_club_or_team_short_name(team)
                    team.save()
                processed_clubs += 1
                self.stdout.write(f"Processed {processed_clubs}/{total_clubs} clubs...")

            self.stdout.write(self.style.SUCCESS("Successfully created short names!"))
