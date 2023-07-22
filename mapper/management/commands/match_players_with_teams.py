from os.path import abspath, isfile

import django.core.exceptions
import pandas as pd
from django.core.management import BaseCommand

from mapper.models import MapperEntity


class Command(BaseCommand):
    """
    Match players with team based on data from xlsx
    """

    def add_arguments(self, parser) -> None:
        parser.add_argument("file_name", type=str)

    def handle(self, *args: any, **options: any) -> None:
        try:
            file_path = abspath(options["file_name"])
        except KeyError:
            raise Exception("Filename not specified.")

        if not isfile(file_path):
            raise Exception("File does not exists.")

        self.import_xlsx(file_path)

    def import_xlsx(self, file: str) -> None:
        PLAYER_ID = "new id from laczynaspilka"
        TEAM_ID = "teamId"

        excel_data = pd.read_excel(file, header=[0])
        data = pd.DataFrame(excel_data)

        for index, row in data.iterrows():
            try:
                team_mapper = MapperEntity.objects.get(mapper_id=row[TEAM_ID])
            except django.core.exceptions.ObjectDoesNotExist:
                continue
            team = team_mapper.target.teamhistory.team

            players_mapper = MapperEntity.objects.filter(mapper_id=row[PLAYER_ID])

            # loop due players duplicates
            for player_mapper_entity in players_mapper:
                player = player_mapper_entity.target.playerprofile
                player.team_object = team
                player.save()
