from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from profiles.models import CoachProfile, PlayerProfile
from users.models import User


class Command(BaseCommand):
    help = "Create PlayerProfile and CoachProfile for users that do not have one"

    def add_arguments(self, parser):
        """
        Add the role and profile type arguments to the command.
        """
        parser.add_argument(
            "role", type=str, help="The role of the user (P for player, T for coach)"
        )

    def handle(self, *args, **options):
        role = options["role"]
        if role != "P" and role != "T":
            raise CommandError(
                "Invalid role specified. Choices are: P for playerprofile, T for coachprofile."
            )
        if role == "P":
            profile_type = PlayerProfile
        else:
            profile_type = CoachProfile
        # Query for users that don't have a specified profile
        users_without_profile = User.objects.filter(declared_role=role).filter(
            Q(playerprofile=None) | Q(coachprofile=None)
        )
        # Create a specified profile instance for each user and save it to the database
        for user in users_without_profile:
            profile = profile_type(user=user)
            profile.save()
        self.stdout.write(
            self.style.SUCCESS(
                "Successfully created {} for all users".format(profile_type.__name__)
            )
        )
