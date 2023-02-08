from django.core.management.base import BaseCommand
import pandas as pd

from profiles.models import PlayerProfile, PlayerVideo


class Command(BaseCommand):
    """
    Match players with their videos based on data from xlsx
    """

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='CSV file to import player videos from')

    def handle(self, *args, **kwargs):
        """
        For each row, the method retrieves the PlayerProfile object that corresponds to the player
        value of the current row and then creates a new PlayerVideo object with the values from
        the current row, or updates an existing one if it already exists. If the PlayerVideo
        object was created, a message is printed indicating the creation of the object.
        If it already existed, a message is printed indicating that the object already exists.
        """
        csv_file = kwargs['csv_file']

        df = pd.read_csv(csv_file)
        player_profiles = PlayerProfile.objects.all()

        for index, row in df.iterrows():
            player_profile = player_profiles.get(user=row['player'])
            player_video, created = PlayerVideo.objects.get_or_create(
                player=player_profile,
                url=row['url'],
                defaults={
                    'title': row['title'] if not pd.isna(row['title']) else "",
                    'description': row['description'] if not pd.isna(row['description']) else '',
                }
            )

            if not created:
                self.stdout.write(f"{player_profile.user} video with url {row['url']} already exists")
            else:
                self.stdout.write(f"{player_profile.user} video with url {row['url']} created")
