import csv
import pprint
from datetime import datetime
from data.models import Player as DPlayer
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from profiles import models
from profiles.views import \
    get_profile_model  # @todo this shoudl goes to utilities, views and commands are using this utility
from users.models import definitions

User = get_user_model()

import logging


logger = logging.getLogger(__name__)



class Command(BaseCommand):
    help = 'Utility to update Players stats'

    def add_arguments(self, parser):
        parser.add_argument('message_type', type=str)
        parser.add_argument(
            '--test',
            type=str,
            help='Used to test message before mass send.',
        )

    def handle(self, *args, **options):

        users = User.objects.filter(declared_role=definitions.PLAYER_SHORT)

        for user in users:
            self.stdout.write(f"###> {user}")
            if not user.is_player:
                self.stdout.write(self.style.ERROR(" #> That user is not a player."))
                continue
            try:
                if user.profile.data_mapper_id is not None and user.profile.league is None:
                    player = DPlayer.objects.get(id=user.profile.data_mapper_id)
                    self.stdout.write(f'updating {player}')
                    try:
                        print(f"mapper_id = {user.profile.data_mapper_id}")
                        start = datetime.now()
                        user.profile.calculate_data_from_data_models()
                        print(f"> calculate_data_from_data_models: {datetime.now()-start}")
                        start = datetime.now()
                        user.profile.trigger_refresh_data_player_stats()  # save not relevant
                        print(f"> trigger_refresh_data_player_stats: {datetime.now()-start}")
                        start = datetime.now()
                        user.profile.fetch_data_player_meta(save=False)  # save comes inside
                        print(f"> fetch_data_player_meta: {datetime.now()-start}")
                        # user.profile.set_team_object_based_on_meta()  # saving
                        start = datetime.now()
                        user.profile.playermetrics.refresh_metrics()  # save not relevant
                        print(f"> refresh_metrics: {datetime.now()-start}")
                        start = datetime.now()
                        user.profile.calculate_fantasy_object()
                        print(f"> calculate_fantasy_object: {datetime.now()-start}")
                        user.profile.save()
                        msg = f'user {user}: player meta_data {player.meta}'
                        self.stdout.write(self.style.SUCCESS(msg))
                    except Exception as e:
                        logger.exception(e)
                        self.stdout.write(self.style.ERROR("Error......"))
                        self.stdout.write(self.style.ERROR(f'ERROR: {e}'))

            except Exception as e:
                logger.exception(e)
                self.stdout.write(self.style.ERROR(f'ERROR: {user} {e}'))
            # if user.profile.data_mapper_id == 9898:
            #     break
            from django.db import reset_queries
            reset_queries()
