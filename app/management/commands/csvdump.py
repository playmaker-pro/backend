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


from .base import BaseCsvDump, BaseCommandCsvHandler


class Command(BaseCommandCsvHandler, BaseCommand, BaseCsvDump):
    help = "Creates CSV data dump. Generates data"

    def handle(self, *args, **options):
        data_rows = []
        _type = options.get("type")
        _marker = options.get("marker")
        if _marker is None:
            raise RuntimeError("Set marker.")

        print(f"Running {_type} csv dumper.")
        if _type == "player":
            _marker += "_player_"
            for player in models.PlayerProfile.objects.all().order_by("user__id"):

                structure = self.get_player_structure(player)
                checksum = self.calculate_checksum(structure)
                structure[self._moderate_field("checksum")] = checksum
                data_rows.append(structure)
        elif _type == "team":
            from clubs.models import Team

            _marker += "_team_"
            for team in Team.objects.all().order_by("id"):
                structure = self.get_team_structure(team)
                checksum = self.calculate_checksum(structure)
                structure[self._moderate_field("checksum")] = checksum
                data_rows.append(structure)
        else:
            raise RuntimeError(
                f"Wrong type of dumper selected (player|team) given:{_type}"
            )

        with open(self.get_csv_name(_marker), mode="w") as csv_file:
            fieldnames = data_rows[0].keys()
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for row in data_rows:
                writer.writerow(row)
