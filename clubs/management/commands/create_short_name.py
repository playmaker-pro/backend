from django.core.management import BaseCommand
from clubs.models import Team, Club
from clubs.management.commands.utils import create_short_name


class Command(BaseCommand):

    def handle(self, *args, **kwargs) -> None:
        """
        This function uses the `create_short_name` method to create a short name for each Club and Team
        in the database.
        The short names are saved to the `club.short_name` and `team.short_name` fields.
        A success message is written to the console for each updated Club and Team.
        """
        clubs = Club.objects.all()
        for club in clubs:
            club_short_name = create_short_name(club)
            club.short_name = club_short_name
            club.save()

            teams = Team.objects.filter(club=club)
            for team in teams:
                team_short_name = create_short_name(team)
                team.short_name = team_short_name
                team.save()

                message = f"Created Team short name {team.short_name} for {team} ({team.id})"
                self.stdout.write(self.style.SUCCESS(message))

            message = f"Created Club short name {club.short_name} for {club} ({club.id})"
            self.stdout.write(self.style.SUCCESS(message))

