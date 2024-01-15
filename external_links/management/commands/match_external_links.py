from typing import Any, Dict, Type
from django.db import models

from django.core.management.base import BaseCommand

from clubs.models import Club, LeagueHistory, Team
from external_links.utils import create_or_update_profile_external_links
from profiles.models import (
    CoachProfile,
    ManagerProfile,
    PlayerProfile,
    ScoutProfile,
    RefereeProfile,
    BaseProfile,
)


class Command(BaseCommand):
    help = (
        "Update or create external links for a specified profile type "
        "or for all types when the '--all' flag is used."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--profile-type",
            type=str,
            help="The type of profile to update or create external links for",
            default=None,
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Process all profile types",
        )

    def handle(self, *args, **options: Dict[str, Any]) -> None:
        """
        This management command allows for the creation or update of ExternalLink objects for profiles.
        When executed with the '--all' flag, the command will update or create external links
        for all supported profile types. If the '--profile-type' flag is provided with a specific
        profile type as its argument, the command will only handle external links for that
        particular type.

        Profile types are mapped to their respective models using the `model_mapping` dictionary.
        For each profile instance of the specified type(s), the command calls the
        `create_or_update_profile_external_links` function. This function is responsible for
        collecting all external links from the profile instance and handling their creation
        or update in the ExternalLinksEntity. Even if a profile doesn't have any existing external
        links, an empty ExternalLink object can be created, which can be subsequently updated
        with new links if needed.

        Upon successful creation or update for each profile type, a success message indicating
        the number of profiles processed will be printed to the console.

        Flags:
            - --profile-type: Specifies the type of profile to process.
            - --all: Process all supported profile types. One of the flags must be provided to
              execute the command.

        Supported profile types:
            - player
            - coach
            - scout
            - manager
            - referee
            - club
            - team
            - league"""

        profile_type = options.get("profile_type")
        process_all = options.get("all")
        valid_types = [
            "player",
            "coach",
            "scout",
            "manager",
            "referee",
            "club",
            "team",
            "league",
        ]
        model_mapping = {
            "player": PlayerProfile,
            "coach": CoachProfile,
            "scout": ScoutProfile,
            "manager": ManagerProfile,
            "referee": RefereeProfile,
            "club": Club,
            "team": Team,
            "league": LeagueHistory,
        }

        if process_all:
            for p_type in valid_types:
                self.update_links_for_type(p_type, model_mapping)
            return

        if profile_type:
            profile_type = profile_type.lower()
            if profile_type not in valid_types:
                self.stdout.write(
                    self.style.ERROR(f"Invalid profile type: {profile_type}")
                )
                return
            self.update_links_for_type(profile_type, model_mapping)
        else:
            self.stdout.write(
                self.style.ERROR(
                    "Please provide a profile type using '--profile-type' or use '--all' to process all profile types."
                )
            )
            return

    def update_links_for_type(
        self, profile_type: str, model_mapping: Dict[str, Type[models.Model]]
    ) -> None:
        """
        Updates external links for a given profile type using the model mapping.

        For each instance of the specified profile type, this method will call the
        `create_or_update_profile_external_links` function to handle the creation or update
        of its external links.

        Args:
            profile_type (str): The type of profile to update or create external links for.
            model_mapping (Dict[str, Type[models.Model]]): A dictionary mapping profile types
            to their respective models.
        """
        model = model_mapping[profile_type]
        profiles = model.objects.all()
        for profile in profiles:
            create_or_update_profile_external_links(profile)

        self.stdout.write(
            self.style.SUCCESS(
                f"External links for {len(profiles)} {profile_type}s updated successfully."
            )
        )
