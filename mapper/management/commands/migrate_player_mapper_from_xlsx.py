from django.core.management import BaseCommand
from os.path import abspath, isfile
import pandas as pd

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

        OLD_LNP_SOURCE_OBJ, _ = MapperSource.objects.get_or_create(name="OLD_LNP")
        NEW_LNP_SOURCE_OBJ, _ = MapperSource.objects.get_or_create(name="NEW_LNP")

        OLD_ID = "mapper id s51 s38"
        OLD_URL = "old link laczynaspilka"
        NEW_ID = "new id from laczynaspilka"
        NEW_URL = "new_link"

        excel_data = pd.read_excel(file, header=[0])
        data = pd.DataFrame(excel_data)

        for index, row in data.iterrows():
            player_qs = PlayerProfile.objects.filter(data_mapper_id=row[OLD_ID])
            for player_obj in player_qs:
                mapper = Mapper.objects.create()
                MapperEntity.objects.create(
                    target=mapper,
                    mapper_id=row[OLD_ID],
                    source=OLD_LNP_SOURCE_OBJ,
                    description="player id from OLD scrapper",
                    url=row[OLD_URL]
                )
                MapperEntity.objects.create(
                    target=mapper,
                    mapper_id=row[NEW_ID],
                    source=NEW_LNP_SOURCE_OBJ,
                    description="player uuid from NEW scrapper",
                    url=row[NEW_URL]
                )
                player_obj.mapper = mapper
                player_obj.save()
