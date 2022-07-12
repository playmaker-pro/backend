from django.core.management import BaseCommand

from django.conf import settings

from voivodeships.models import Voivodeships


class Command(BaseCommand):
    help = "Create voivodeships"

    def handle(self, *args, **options):

        for voivodeship in settings.VOIVODESHIP_CHOICES:

            assert isinstance(voivodeship, tuple), "element is not a tuple"
            voivodeship = voivodeship[0]

            try:

                assert isinstance(voivodeship, str), f"{voivodeship} is not a string"
                obj, created = Voivodeships.objects.get_or_create(
                    name=voivodeship
                )

                if created:
                    self.stdout.write(f'voivodeship {voivodeship} has been added')
                else:
                    self.stdout.write(f'voivodeship {voivodeship} already exists in database')

            except Exception as e:
                self.stdout.write(f'{voivodeship}', e)