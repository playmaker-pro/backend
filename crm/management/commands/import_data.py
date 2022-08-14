from django.core.management.base import BaseCommand, CommandError
from crm.scripts.xlsx_import import ImportFromXlsx

"""
file_path - drag and drop file from files explorer into terminal 
"""

class Command(BaseCommand):
    help = "Pass argument as xlsx file path to import data"
    
    def add_arguments(self, parser) -> None:
        parser.add_argument("file_path", type=str)  
    
    def handle(self, *args, **options):
        file = options["file_path"]
        try:
            ImportFromXlsx(file)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"{file} not found. Wrong path."))
            
        self.stdout.write(self.style.SUCCESS(f"Successfully imported {file} into crm app."))