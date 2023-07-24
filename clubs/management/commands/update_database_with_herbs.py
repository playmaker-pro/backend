import json

from clubs.models import Club
from django.core.management import BaseCommand

from .utils import PATH_TO_FILE, PATH_TO_FLAGS, change_club_image

PATH_TO_FLAGS = f"{PATH_TO_FLAGS}\\"


class Command(BaseCommand):
    """Update database"""

    def handle(self, *args: any, **options: any) -> None:

        clubs = Club.objects.all()

        try:

            with open(PATH_TO_FILE, "r", encoding="utf-8") as f:
                clubs_matched = json.load(f)
            change_club_image(clubs, clubs_matched)

        except FileNotFoundError as e:
            print(e)
