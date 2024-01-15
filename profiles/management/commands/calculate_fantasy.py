from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Utility to update Players Fantasy"

    def handle(self, *args, **options):
        users = self.get_queryset()
        self.stdout.write(
            self.style.SUCCESS(
                f"Starting to calculate fantasy objects. Following number of objects will be updated {users.count()}"
            )
        )
        for user in users:
            if user.is_player:
                try:
                    if user.profile.attached:
                        self.stdout.write(f">> updating {user}")
                        try:
                            user.profile.calculate_fantasy_object()
                            user.profile.save()
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"error: {e}"))
                        msg = f"User {user} fantasy metrics updated."
                        self.stdout.write(self.style.SUCCESS(msg))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"{user} {e}"))

    def add_arguments(self, parser):
        parser.add_argument("message_type", type=str)
        parser.add_argument(
            "--test",
            type=str,
            help="Used to test message before mass send.",
        )

    def get_queryset(self):
        return User.objects.all()
