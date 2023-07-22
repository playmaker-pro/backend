from django.core.management import BaseCommand

from clubs.models import Club

from .utils import get_club_without_img


class Command(BaseCommand):
    """
    Get clubs without herbs
    """

    def handle(self, *args: any, **options: any) -> None:
        clubs = Club.objects.exclude(teams=None)
        clubs = get_club_without_img(clubs, herbs=True)

        print(clubs)
