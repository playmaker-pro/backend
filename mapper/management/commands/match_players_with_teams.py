from django.core.management import BaseCommand
from os.path import abspath, isfile
import pandas as pd
from mapper.models import MapperEntity


class Command(BaseCommand):
    """
    Match players with team based on data from xlsx
    """

    def add_arguments(self, parser) -> None:
        parser.add_argument('file_name', type=str)

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
        TEAM_ID = "teamid"

        excel_data = pd.read_excel(file, header=[0])
        data = pd.DataFrame(excel_data)

        for index, row in data.iterrows():

            team_mapper = MapperEntity.objects.get(mapper_id=row[TEAM_ID])
            team = team_mapper.target.teamhistory.team

            player_mapper = MapperEntity.objects.get(mapper_id=row[PLAYER_ID])
            player = player_mapper.target.playerprofile

            player.team = team
            player.save()
