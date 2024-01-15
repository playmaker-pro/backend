import csv

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Load dumped profiles from csv file."

    def add_arguments(self, parser):
        parser.add_argument("path", type=str)

    def handle(self, *args, **options):
        with open(options["path"], newline="") as csvfile:
            reader = csv.DictReader(csvfile)

            for i, row in enumerate(reader):
                email = row["email_user"]
                first_name, _ = email.split("@")
                last_name, _ = email.split("@")
                initial_password = "123!@#qweQWE"
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    user = User.objects.create_user(
                        email=email.lower(),
                        first_name=first_name,
                        last_name=last_name,
                        password=initial_password,
                        declared_role=None,
                    )
