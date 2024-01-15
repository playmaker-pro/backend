import csv
import pprint

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

# from data.models import Player    DEPRECATED: PM-1015
from profiles import models
from profiles.views import (
    get_profile_model,
)  # @todo this shoudl goes to utilities, views and commands are using this utility

User = get_user_model()


class Command(BaseCommand):
    help = "Load dumped profiles from csv file."

    def add_arguments(self, parser):
        parser.add_argument("path", type=str)
        parser.add_argument("off", type=str)

    def position_map(self, param, leg):
        """
        W bazie wix jest Obrońca - boczny. Dopasowanie prawy / lewy jest w przypadku
        position = "Obrońca boczny" & foot = "Prawa" => "Obrońca Prawy"
        position = "Obrońca boczny" & foot = "Lewa" => "Obrońca Lewy"

        POSITION_CHOICES = [
            (1, 'Bramkarz'),
            (2, 'Obrońca Lewy'),
            (3, 'Obrońca Prawy'),
            (4, 'Obrońca Środkowy'),
            (5, 'Pomocnik defensywny (6)'),
            (6, 'Pomocnik środkowy (8)'),
            (7, 'Pomocnik ofensywny (10)'),
            (8, 'Skrzydłowy'),
            (9, 'Napastnik'),
        ]
        """
        if param is None:
            return None
        if param.lower() == "obrońca boczny" and leg == "Lewa":
            return 2
        if param.lower() == "obrońca - wahadłowy" and leg == "Lewa":
            return 2
        elif param.lower() == "obrońca boczny" and leg == "Prawa":
            return 3
        elif param.lower() == "obrońca - wahadłowy" and leg == "Prawa":
            return 3
        elif param.lower() == "obrońca - środkowy":
            return 4
        elif param.lower() == "bramkarz":
            return 1
        elif param.lower() == "pomocnik - defensywny (6)":
            return 5
        elif param.lower() == "pomocnik - środkowy (8)":
            return 6
        elif param.lower() == "pomocnik - ofensywny (10)":
            return 7
        elif param.lower() == "skrzydłowy":
            return 8
        elif param.lower() == "npastnik":
            return 9
        elif param.lower() == "obrońca - wahadłowy":
            return 3
        else:
            return None

    def phone_map(self, param):
        if param is None:
            return None
        if len(param) == 9:
            return "+48" + param
        if param.startswith("+") and len(param) == 12:
            return param

    def get_param_or_none(self, row, param_name):
        return row[param_name] if row[param_name] != "" else None

    def handle(self, *args, **options):
        with open(options["path"], newline="") as csvfile:
            reader = csv.DictReader(csvfile)

            for i, row in enumerate(reader):
                # if i < 335:
                #     continue
                # print(row['address2'])
                # continue
                self.stdout.write(self.style.SUCCESS(pprint.pprint(row)))

                if options["off"] == "T":
                    email = "jacek.jasinski8@gmail.com"
                else:
                    email = row["wix_id"]
                    if email == "":
                        continue

                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    continue

                prefered_leg = self.get_param_or_none(row, "foot")
                position_raw = self.get_param_or_none(row, "position")
                position_raw_alt = self.get_param_or_none(row, "alternative_position")

                profile = user.profile

                profile.position_raw = self.position_map(position_raw, prefered_leg)
                profile.position_raw_alt = self.position_map(
                    position_raw_alt, prefered_leg
                )

                user.profile.save(silent=True)
                if options["off"] == "T":
                    break

        # user = User.objects.create_user(username='john',
        #                          email='jlennon@beatles.com',
        #                          password='glass onion')
        # for poll_id in options['poll_ids']:
        #     try:
        #         poll = Poll.objects.get(pk=poll_id)
        #     except Poll.DoesNotExist:
        #         raise CommandError('Poll "%s" does not exist' % poll_id)

        #     poll.opened = False
        #     poll.save()

        # self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))
