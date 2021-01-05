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
    messages = {'weekly': weekly_account_report}

    help = 'Command line to send requests to users.'

    def add_arguments(self, parser):
        parser.add_argument('message_type', type=str)
        parser.add_argument(
            '--test',
            type=str,
            help='Used to test message before mass send.',
        )

    def handle(self, *args, **options):
        if options['test']:
            email = options['test']
            qs = self.get_user_queryset(email=email)
        else:
            qs = self.get_user_model()

        return self.handle_weekly(qs, *args, **options)

    def handle_weekly(self, qs, *args, **options):
        method = self.get_message('weekly')
        for obj in qs:
            method(obj)
            self.stdout.write(self.style.SUCCESS(f'Message sended. to {obj.email}'))

    def get_message(self, msg_type):
        if msg_type in self.messages:
            return self.messages[msg_type]
        else:
            return None
            self.stdout.write(self.style.ERROR('There is no such a type of message.'))

    def get_user_queryset(self, email=None):
        qs = User.objects.all()
        if email:
            return qs.filter(email=email)
        else:
            return qs.filter(notificationsetting__weekly_report=False)
