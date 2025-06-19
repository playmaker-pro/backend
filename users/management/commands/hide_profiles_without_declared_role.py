from django.core.management.base import BaseCommand

from users.models import User


class Command(BaseCommand):
    help = "Hide profiles without the declared_role"

    def handle(self, *args, **kwargs):
        users = User.objects.filter(declared_role__isnull=True)

        for user in users:
            user.display_status = User.DisplayStatus.NOT_SHOWN
            user.save(update_fields=["display_status"])
