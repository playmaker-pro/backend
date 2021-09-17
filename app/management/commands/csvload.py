from django.core.management.base import BaseCommand, CommandError
import csv
from data.models import Player
from profiles import models 
from profiles.views import get_profile_model   # @todo this shoudl goes to utilities, views and commands are using this utility
from django.contrib.auth import get_user_model
import pprint
from .base import BaseCsvDump, BaseCommandCsvHandler
from clubs.models import Team

User = get_user_model()


class Command(BaseCommandCsvHandler, BaseCommand, BaseCsvDump):
    help = "Uploads data from csv"


    def handle(self, *args, **options):

        _type = options.get("type")
        _marker = options.get("marker")
        _dryrun = options.get("dryrun")

        if _dryrun is not None:
            print(f"Dryrunmode set to: {_dryrun}")

        if _marker is None:
            raise RuntimeError("Set marker.")

        print(f"Running {_type} csv laader.")

        if _type == "player":
            _marker += "_player_"
        elif _type == "team":
            _marker += "_team_"
        csv_name = self.get_csv_name(_marker)
        print(f"Reading file: {csv_name}")
        with open(csv_name, newline='') as csvfile:
            data = csv.DictReader(csvfile)
            if _type == "player":
                self.handle_player_changes(data, _dryrun)
              
            elif _type == "team":
                self.handle_team_changes(data, _dryrun)


    def handle_team_changes(self, rows, _dryrun):
        for row in rows:
            object_id = row.get(self._read_field("id"))
            team = Team.objects.get(id=object_id)
            changed_league_object_id = row.get(self._write_field("league_object"))
            changed_mapping = row.get(self._write_field("mapping"))
            changed_club_object_id = row.get(self._write_field("club_object"))
            if any([changed_league_object_id, changed_mapping, changed_club_object_id]):
                print(f"ROW: New value for team detected for {team}")
                structure = self.get_team_structure(team)
                checksum = self.calculate_checksum(structure)
                previous_checksum = row.get(self._get_checksum_field())
                if previous_checksum != checksum:
                    print(f'Save for that row not possible. Checksums are different.')  
                    continue
                else:
                    from clubs.models import League, Club
                    if changed_mapping:
                        team.mapping = changed_mapping
                    if changed_league_object_id:
                        team.league = League.objects.get(id=changed_league_object_id)
                    if changed_club_object_id:
                        team.club = Club.objects.get(id=changed_club_object_id)

                    print(f'Saving Team data {team} mapping={changed_mapping}, league_id={changed_league_object_id}, club_id={changed_club_object_id}')
                    if _dryrun:
                        print("skiping save...")
                    else:
                        team.save()

    def handle_player_changes(self, rows, _dryrun):
        for row in rows:
            object_id = row.get(self._read_field("id"))
            player = models.PlayerProfile.objects.get(user=object_id)
            team_object_id = row.get(self._write_field("team_object"))
            if team_object_id:
                print(f"ROW: New value for team_object detected for {player}")
                structure = self.get_player_structure(player)
                checksum = self.calculate_checksum(structure)
                previous_checksum = row.get(self._get_checksum_field())
                if previous_checksum != checksum:
                    print(f'Save that row not possible. Checksums are different.')  
                    continue
                else:
                    print(f'Saving new team with id={team_object_id} to {player}')
                    msg = f"CSVDump changing team_object_id={player.team_object.id if player.team_object else None } to new one team_object_id={team_object_id}"
                    player.add_event_log_message(msg)
                    player.team_object = Team.objects.get(id=team_object_id)
                    if _dryrun:
                        print("skiping save...")
                    else:
                        player.save()
