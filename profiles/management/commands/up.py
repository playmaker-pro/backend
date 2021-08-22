from django.core.management.base import BaseCommand, CommandError
import csv
from data.models import Player
from profiles import models 
from profiles.views import get_profile_model   # @todo this shoudl goes to utilities, views and commands are using this utility
from django.contrib.auth import get_user_model
import pprint

User = get_user_model()


class Command(BaseCommand):
    help = 'Update metrics..for Coaches.'

    def handle(self, *args, **options):
        profiles = models.CoachProfile.objects.filter(data_id_mapper__isnull=False)

        for prof in profiles:
            self.stdout.write(self.style.SUCCESS(f"Updating... {prof.user} profile: {prof}"))
            prof.calculate_metrics()
            self.stdout.write(self.style.SUCCESS(f"Done."))
