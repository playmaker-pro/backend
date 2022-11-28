from os.path import abspath, isfile

from django.core.management import BaseCommand

from crm.scripts.xlsx_import import ImportFromXlsx


class Command(BaseCommand):
    """
    Import CRM data from xlsx
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

        delivery = ImportFromXlsx(file_path)
        delivery.bulk_xlsx_import()
