import csv
import pprint

from data.models import Player
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from notifications.mail import weekly_account_report
from notifications import models


User = get_user_model()


class Command(BaseCommand):
    help = 'Creates initial account settings'

    def add_arguments(self, parser):
        parser.add_argument('type', type=str)

    def handle(self, *args, **options):
        testrun = options['type']
        if '@' in testrun:
            user = User.objects.get(email=testrun)
            _, _ = models.NotificationSetting.objects.get_or_create(user=user)
        else:
            us = User.objects.all()
            for user in us:
                _, _ = models.NotificationSetting.objects.get_or_create(user=user)
            self.stdout.write(self.style.SUCCESS(f'Settings refreshed for {us.count()}'))
