import logging
from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import reset_queries
from profiles import models
from profiles.views import (
    get_profile_model,
)  # @todo this shoudl goes to utilities, views and commands are using this utility
from users.models import definitions

User = get_user_model()


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Utility to update Players stats"

    def add_arguments(self, parser):
        parser.add_argument("method", type=str, default="all")
        parser.add_argument(
            "--test",
            type=str,
            help="Used to test message before mass send.",
        )

    def handle(self, *args, **options):
        selected_method = options.get("method")

        players = models.PlayerProfile.objects.filter(
            user__declared_role=definitions.PLAYER_SHORT, data_mapper_id__isnull=False
        )
        methods = [
            ("calculate_data_from_data_models", (), {}),
            ("trigger_refresh_data_player_stats", (), {}),
            ("fetch_data_player_meta", (), {"save": False}),
            ("refresh_metrics", (), {}),
            ("calculate_fantasy_object", (), {}),
        ]
        for player in players:
            self.stdout.write(f"###> {player}")
            if not player.user.is_player:
                self.stdout.write(
                    self.style.ERROR(" ERROR > That user is not a player.")
                )
                continue

            if player.data_mapper_id and player.league:
                self.stdout.write(
                    self.style.ERROR(
                        " ERROR > That user profile do not have data_mapper_id set."
                    )
                )
                continue
            try:
                self.stdout.write(f"updating {player}")
                try:
                    print(f"mapper_id = {player.data_mapper_id}")
                    start = datetime.now()

                    for method, args, kwargs in methods:
                        if selected_method != "all":
                            start = datetime.now()
                            getattr(player, method)(*args, **kwargs)
                            print(f"> \t calc: {method}: {datetime.now() - start}")
                        elif selected_method == method:
                            start = datetime.now()
                            getattr(player, method)(*args, **kwargs)
                            print(f"> \t calc: {method}: {datetime.now() - start}")
                    player.save()

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"ERROR > : {e}"))
                    logger.exception(e)

            except Exception as e:
                logger.exception(e)
                self.stdout.write(self.style.ERROR(f"ERROR: {player} {e}"))

            reset_queries()
