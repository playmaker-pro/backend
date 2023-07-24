from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from profiles import models


User = get_user_model()


class Command(BaseCommand):
    help = "Update metrics..for Coaches."

    def add_arguments(self, parser):
        """
        :deep:
            defines how many seasons behind current one we want to go
            by default it is set to 1 which basicaly means get current season.
        """
        parser.add_argument("-d", "--deep", type=int, default=1)
        parser.add_argument("-s", "--season", type=str, default=None)

    def handle(self, *args, **options):
        deep = options.get("deep")
        season_name = options.get("season")

        profiles = models.CoachProfile.objects.filter(
            mapper__mapperentity__related_type='coach',
            mapper__mapperentity__database_source='s38',
            mapper__mapperentity__mapper_id__isnull=False
        )
        counter = profiles.count()
        if counter == 0:
            self.stdout.write("No profiles to update...")
        for profile in profiles:
            self.stdout.write(
                self.style.SUCCESS(f"Updating... {profile.user} profile: {profile}")
            )
            profile.calculate_metrics(seasons_behind=deep, season_name=season_name)
            self.stdout.write(self.style.SUCCESS("Done :)"))
