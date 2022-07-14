from django.core.management.base import BaseCommand, CommandError
import csv
from data.models import Player
from profiles import models
from profiles.views import (
    get_profile_model,
)  # @todo this shoudl goes to utilities, views and commands are using this utility
from django.contrib.auth import get_user_model
import pprint

User = get_user_model()


class Command(BaseCommand):
    help = "Force to create Verfication object for all of users."

    def handle(self, *args, **options):
        ...
