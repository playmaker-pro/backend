from django.core.management.base import BaseCommand

from profiles.models import PROFILE_MODELS, BaseProfile


class Command(BaseCommand):
    help = "Create/update new uuid for each Profile"

    def confirm(self) -> bool:
        """Display warning and return decision"""
        print(
            "\n\nTHIS COMMAND WILL PERMANENTLY CHANGE ALL UUIDS\n"
            "AMONG PROFILES AND MAY CAUSE DATA INCOHERENCE\n"
            "TYPE 'OK' IF YOU WANT TO CONTINUE PROCESS"
        )
        return input("> ").upper() == "OK"

    def handle(self, *args, **options) -> None:
        """
        Iterate through each type of profile, then through each profile object
        Set/overwrite new uuid for profile, log results
        """
        if not self.confirm():
            print("Aborted")
            return

        for profile_type in PROFILE_MODELS:
            if profile_type is BaseProfile:
                continue

            for profile in profile_type.objects.all():
                try:
                    profile.generate_uuid(force=True)
                    print(f"New UUID: {profile.uuid} for {profile}.")
                except Exception as e:
                    print(e)
