from clubs.models import Team, Club, LeagueHistory, TeamHistory, League
from connector.scripts.base import BaseCommand
from mapper.models import MapperEntity


class Command(BaseCommand):
    """
    Restore database from scrapper changes
    """
    def handle(self):
        for e in MapperEntity.objects.all():
            e.delete()

        for team in Team.objects.filter(scrapper_autocreated=True):
            team.delete()

        for club in Club.objects.filter(scrapper_autocreated=True):
            club.delete()

        # for team in Team.objects.filter(scrapper_teamhistory_id__isnull=False):
        for team in Team.objects.filter(mapper__isnull=False):
            entities = MapperEntity.objects.filter(target=team.mapper)
            for entity in entities:
                entity.delete()

        for club in Club.objects.filter(mapper__isnull=False):
            entities = MapperEntity.objects.filter(target=club.mapper)
            for entity in entities:
                entity.delete()
            # club.scrapper_uuid = None
            # club.save()

        for league in League.objects.filter(scrapper_autocreated=True):
            league.delete()

        for lh in LeagueHistory.objects.all():
            lh.mapper.delete()
            lh.delete()

        for th in TeamHistory.objects.all():
            th.mapper.delete()
            th.delete()
