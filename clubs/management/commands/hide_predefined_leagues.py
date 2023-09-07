from django.core.management import BaseCommand
from django.db.models import QuerySet

from clubs.models import League


class Command(BaseCommand):
    """Hide predefined leagues"""

    LEAGUES_TO_HIDE = [
        "II Liga PLF K",
        "Futsal Ekstraklasa",
        "Liga Makroregionalna U-19",
        "I Liga PLF K",
        "I Liga PLF",
        "II Liga PLF",
        "III Liga PLF",
        "Ekstraliga PLF K",
    ]

    def handle(self, *args: any, **options: any) -> None:
        leagues: QuerySet[League] = League.objects.filter(name__in=self.LEAGUES_TO_HIDE)
        for league in leagues:
            league.visible = False
            league.save()
