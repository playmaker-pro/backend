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

        for user in users:
            if user.is_player:
                try:
                    if user.profile.data_mapper_id is not None and user.profile.league is None:
                        player = Player.objects.get(id=user.profile.data_mapper_id)
                        user.profile.calculate_data_from_data_models()
                        user.profile.save()
                        msg = f'user {user}: player meta_data {player.meta}'
                        self.stdout.write(self.style.SUCCESS(msg))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'{user} {e}'))
