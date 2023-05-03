from clubs.models import Club, League, LeagueHistory, Team, TeamHistory
from connector.scripts.base import BaseCommand
from mapper.models import Mapper, MapperEntity


class Command(BaseCommand):
    """
    Restore database from scrapper changes
    """

    def handle(self, *args, **kwargs):
        # Mapper.objects.all().delete()

        for team in Team.objects.filter(scrapper_autocreated=True):
            team.mapper.delete()
            team.delete()

        for club in Club.objects.filter(scrapper_autocreated=True):
            club.mapper.delete()
            club.delete()

        for team in Team.objects.filter(mapper__isnull=False):
            entities = team.mapper.get_entities()
            for entity in entities:
                entity.delete()

        for club in Club.objects.filter(mapper__isnull=False):
            entities = club.mapper.get_entities()
            for entity in entities:
                entity.delete()

        for league in League.objects.filter(scrapper_autocreated=True):
            league.delete()

        for lh in LeagueHistory.objects.all():
            if lh.mapper:
                lh.mapper.delete()
            lh.delete()

        for th in TeamHistory.objects.all():
            for entity in th.mapper.get_entities():
                entity.delete()
            th.delete()
