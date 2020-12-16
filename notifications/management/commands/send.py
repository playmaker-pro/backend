from django.core.management.base import BaseCommand, CommandError
import csv
from data.models import Player
from profiles import models 
from profiles.views import get_profile_model   # @todo this shoudl goes to utilities, views and commands are using this utility
from django.contrib.auth import get_user_model
import pprint
from notifications.mail import weekly_account_report

User = get_user_model()


class Command(BaseCommand):
    help = 'Command line to send requests to users.'

    def add_arguments(self, parser):
        parser.add_argument('test_mail', type=str)

    def handle(self, *args, **options):
        email = options['test_mail']
        u = User.objects.get(email=email)
        weekly_account_report(u)
        self.stdout.write(self.style.SUCCESS('Message sended.'))
