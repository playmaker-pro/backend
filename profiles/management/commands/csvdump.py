from django.core.management.base import BaseCommand, CommandError
import csv
from data.models import Player
from profiles import models 
from profiles.views import get_profile_model   # @todo this shoudl goes to utilities, views and commands are using this utility
from django.contrib.auth import get_user_model
import pprint

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates CSV data dump.'


    def handle(self, *args, **options):
        data_rows = []
        for player in models.PlayerProfile:
            data_rows.append(
                {
                    '(R) full_name': player.user.get_full_name(),
                    '(R) display_team': player.display_team,
                    '(R) display_league': player.display_league
                }
            )

        with open('playmaker_dump_v1.csv', mode='w') as csv_file:
            fieldnames = ['(R) full_name', '(R) display_team', '(R) display_league']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for row in data_rows:
                writer.writerow(row)
