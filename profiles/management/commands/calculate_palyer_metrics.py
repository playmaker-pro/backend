import logging
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import reset_queries

# from data.models import Player    DEPRECATED: PM-1015
from profiles import models
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
            user__declared_role=definitions.PLAYER_SHORT,
            mapper__mapperentity__related_type="player",
            mapper__mapperentity__database_source="s38",
            mapper__mapperentity__mapper_id__isnull=False,
            user__last_login__gt=datetime.now() - timedelta(days=30),
        )

        methods = [
            ("calculate_data_from_data_models", (), {}),
            ("trigger_refresh_data_player_stats", (), {}),
            ("fetch_data_player_meta", (), {"save": False}),
            ("refresh_metrics", (), {}),
            ("calculate_fantasy_object", (), {}),
        ]
        for player in players.iterator():
            player_mapper = player.mapper.get_entity(
                related_type="player", database_source="s38"
            ).mapper_id
            self.stdout.write(f"###> {player}")
            if not player.user.is_player:
                self.stdout.write(
                    self.style.ERROR(" ERROR > That user is not a player.")
                )
                continue

            if not player_mapper and player.league:
                self.stdout.write(
                    self.style.ERROR(
                        f" ERROR > That user profile do not have mapper={player_mapper} set or it has league={player.league}"
                    )
                )
                continue
            try:
                self.stdout.write(f"updating {player}")
                try:
                    print(f"mapper_id = {player_mapper}")
                    start = datetime.now()

                    for method, args, kwargs in methods:
                        if selected_method == "all":
                            self.execute_method(player, method, *args, **kwargs)
                        elif selected_method == method:
                            self.execute_method(player, method, *args, **kwargs)
                    player.save()
                    print("-----------")

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"ERROR > : {e}"))
                    logger.exception(e)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"ERROR: {player} {e}"))
                logger.exception(e)

            reset_queries()

    def execute_method(
        self, profile: models.PlayerProfile, method: str, *args, **kwargs
    ):
        start = datetime.now()
        getattr(profile, method)(*args, **kwargs)
        print(f"> \t calc: {method}: {datetime.now() - start}")
