from django.core.management.base import BaseCommand, CommandError
import csv
from data.models import Player
from profiles import models 
from profiles.views import get_profile_model   # @todo this shoudl goes to utilities, views and commands are using this utility
from django.contrib.auth import get_user_model
import pprint

from data.models import Player


User = get_user_model()


class Command(BaseCommand):
    help = 'Utility to update Players stats'

    def add_arguments(self, parser):
        parser.add_argument('message_type', type=str)
        parser.add_argument(
            '--test',
            type=str,
            help='Used to test message before mass send.',
        )

    def get_queryset(self):
        return User.objects.all()

    def filter_queryset(self, queryset, options):
        if options['test']:
            email = options['test']
            queryset = queryset.filter(email=email)
        return queryset

    def handle(self, *args, **options):
        users = self.get_queryset()
        users = self.filter_queryset(users, options)
        self.stdout.write(self.style.SUCCESS(f'Starting to calculate fantasy objects. Following number of objects will be updated {users.count()}'))
        for user in users:
            if user.is_player:
                try:
                    if user.profile.data_mapper_id is not None and user.profile.league is None:
                        player = Player.objects.get(id=user.profile.data_mapper_id)
                        self.stdout.write(f'updating {player}')
                        try:
                            user.profile.calculate_fantasy_object()
                            user.profile.save()
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'error: {e}'))
                        msg = f'user {user}: player meta_data {player.meta}'
                        self.stdout.write(self.style.SUCCESS(msg))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'{user} {e}'))
