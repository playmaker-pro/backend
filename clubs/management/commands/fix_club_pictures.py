from django.core.management import BaseCommand

from clubs.models import Club

char_mapper = str.maketrans("ŁŚŻ", "£¦¯")  # add other chars mapping if occurs again


class Command(BaseCommand):
    def fix_filename(self, filename: str) -> str:
        """Change broken char in image filename"""
        return filename.translate(char_mapper)

    def handle(self, *args, **options) -> None:
        """Loop through clubs. If club has picture,
        change its name with predefined char mapper"""
        for club in Club.objects.all():
            if club.picture and club.picture.name:
                club.picture.name = self.fix_filename(club.picture.name)
                club.save()
