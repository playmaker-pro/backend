from django.core.management import BaseCommand
from django.db.models import QuerySet

from clubs.models import League, Seniority


class Command(BaseCommand):
    """Change league seniority to "Centralna Liga Juniorow" if requires are satisfied"""

    CENTRAL_JUNIOR_LEAGUE_NAME = "Centralna Liga Juniorow"
    LEAGUES_TO_CHANGE = [
        "CLJ U-19",
        "Liga Makroregionalna U-19",
        "CLJ U-18",
        "CLJ U-17",
        "CLJ U-15",
        "CLJ U-17 K",
        "CLJ U-15 K",
    ]

    @property
    def is_central_junior_seniority_in_db(self) -> Seniority:
        """Returns True if Centralna Liga Juniorow seniority object is in db"""
        return Seniority.objects.filter(name=self.CENTRAL_JUNIOR_LEAGUE_NAME).exists()

    @property
    def central_league_seniority(self) -> Seniority:
        """Returns Centralna Liga Juniorow seniority object"""
        return Seniority.objects.get(name=self.CENTRAL_JUNIOR_LEAGUE_NAME)

    def handle(self, *args: any, **options: any) -> None:
        """
        Change league seniority to "Centralna Liga Juniorow"
        if requires are satisfied
        """
        if not self.is_central_junior_seniority_in_db:
            self.create_new_central_junior_seniority()
        leagues = League.objects.filter(name__in=self.LEAGUES_TO_CHANGE)
        self.change_league_seniority(leagues=leagues)

    def change_league_seniority(self, leagues: QuerySet[League]):
        """
        Change league seniority to "Centralna Liga Juniorow"
        for given objects in QuerySet
        """
        for league in leagues:
            league.seniority = self.central_league_seniority
            league.save()

    def create_new_central_junior_seniority(self):
        """
        Create new seniority object with name "Centralna Liga Juniorow"
        and is_senior=False
        """
        seniority = Seniority(name=self.CENTRAL_JUNIOR_LEAGUE_NAME, is_senior=False)
        seniority.save()
