import json
import os

from django.core.management import BaseCommand
from clubs.models import Club

from .utils import PATH_TO_FLAGS, change_club_image, PATH_TO_LOG

PATH_TO_FLAGS = f'{PATH_TO_FLAGS}\\'


class Command(BaseCommand):

    def handle(self, *args: any, **options: any) -> None:
        """ Update production database """

        clubs = Club.objects.all()

        try:
            with open(os.path.join(PATH_TO_LOG, 'final_result.txt'), 'r', encoding="utf-8") as f:
                clubs_matched = json.load(f)

            change_club_image(clubs, clubs_matched)

        except FileNotFoundError as e:
            print(e)
