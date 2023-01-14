from django.core.management import BaseCommand
from os.path import abspath, isfile
import pandas as pd
from django.db.models import Q

from mapper.models import Mapper, MapperEntity, MapperSource
from profiles.models import PlayerProfile


class Command(BaseCommand):
    """
    Import player ids/urls from xlsx to new mapper
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

        OLD_ID = "mapper id s51 s38"
        OLD_URL = "old link laczynaspilka"
        NEW_ID = "new id from laczynaspilka"
        NEW_URL = "new_link"
        PM_URL = "link playmaker pro"

        excel_data = pd.read_excel(file, header=[0])
        data = pd.DataFrame(excel_data)

        for index, row in data.iterrows():
            """
            For each row, the script is querying the PlayerProfile model to retrieve any player objects 
            that have a data_mapper_id value that matches the OLD_ID value in the current row, 
            or a slug value that matches the last element in the PM_URL value split by the '/' character. 
            The resulting queryset is stored in the variable player_qs.
            """
            player_qs = PlayerProfile.objects.filter(
                Q(data_mapper_id=row[OLD_ID]) | Q(slug=row[PM_URL].split("/")[-1])
            )
            for player_obj in player_qs:
                mapper = Mapper.objects.create()
                MapperEntity.objects.create(
                    target=mapper,
                    mapper_id=row[OLD_ID],
                    description="player id from OLD scrapper",
                    url=row[OLD_URL],
                    database_source="s38"
                )
                MapperEntity.objects.create(
                    target=mapper,
                    mapper_id=row[NEW_ID],
                    description="player uuid from NEW scrapper",
                    url=row[NEW_URL],
                    database_source="scrapper_mongodb"
                )
                player_obj.mapper = mapper
                player_obj.save()
