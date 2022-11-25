from clubs.models import Team, Club, LeagueHistory, TeamHistory, League
from connector.scripts.base import BaseCommand


class Command(BaseCommand):
    """
    Restore database from scrapper changes
    """
    def handle(self):

        for team in Team.objects.filter(scrapper_autocreated=True):
            team.delete()

        for club in Club.objects.filter(scrapper_autocreated=True):
            club.delete()

        for team in Team.objects.filter(scrapper_teamhistory_id__isnull=False):
            team.scrapper_teamhistory_id = None
            team.save()

        for club in Club.objects.filter(scrapper_uuid__isnull=False):
            club.scrapper_uuid = None
            club.save()

        for league in League.objects.filter(scrapper_autocreated=True):
            league.delete()

        for lh in LeagueHistory.objects.all():
            lh.delete()

        for th in TeamHistory.objects.all():
            th.delete()
