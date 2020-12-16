from django.core.management.base import BaseCommand, CommandError
import csv
from data.models import Player
from profiles import models 
from profiles.views import get_profile_model   # @todo this shoudl goes to utilities, views and commands are using this utility
from django.contrib.auth import get_user_model
import pprint


User = get_user_model()


class Command(BaseCommand):
    help = 'Load dumped profiles from csv file.'

    def add_arguments(self, parser):
        parser.add_argument('path', type=str)
        parser.add_argument('type', type=str)

    def handle(self, *args, **options):
        role = options['type']
        self.stdout.write(self.style.SUCCESS(pprint.pprint(row)))
        