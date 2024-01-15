import glob
import os.path

from django.core.management import BaseCommand
from django.db.models import Q

from clubs.models import Club

char_file_pattern_mapper = str.maketrans(
    "ŁŚŻ£¦¯", "******"
)  # add other chars mapping if occurs again


class Command(BaseCommand):
    def handle(self, *args, **options) -> None:
        """
        Loop through clubs containing selected letters.

        This command iterates over Club objects whose names contain at least one
        of the characters 'Ł', 'Ś', or 'Ż'. For each Club, it attempts to locate an
        image file based on the modified file path pattern generated from the original
        picture path. If successful, it updates the picture field with the new image.

        The 'char_file_pattern_mapper' is a character mapping used to modify the file
        path pattern, replacing occurrences of 'Ł', 'Ś', and 'Ż' with '***'. Additional
        character mappings can be added if needed.
        """
        for club in Club.objects.filter(
            Q(name__contains="Ł") | Q(name__contains="Ś") | Q(name__contains="Ż")
        ):
            if club.picture and club.picture.name:
                pattern = club.picture.path.translate(char_file_pattern_mapper)
                pattern = pattern.replace(pattern.split("/")[-2], "**")

                try:
                    filepath = glob.glob(pattern, recursive=True)[0]
                except IndexError:
                    print("Błąd ", club.picture.name, pattern)
                    continue

                filename = os.path.basename(filepath)

                with open(filepath, "rb") as image:
                    club.picture.save(name=filename, content=image)
                    print("Updated")
