from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Set display_status=NOT_SHOWN for users with the same first and last name"

    def handle(self, *args, **options):
        for user in User.objects.exclude(display_status=User.DisplayStatus.NOT_SHOWN):
            if user.first_name == user.last_name:
                user.display_status = User.DisplayStatus.NOT_SHOWN
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"User {user.get_full_name()} [pk={user.pk}] "
                        "display status set to NOT_SHOWN."
                    )
                )
