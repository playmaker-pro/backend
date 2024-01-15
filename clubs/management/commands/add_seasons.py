import re

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction

from clubs import services


class Command(BaseCommand):
    """
    Management command to add a range of seasons to the database.

    This command accepts a start and end year, and creates seasons
    for each year in that range. Each season is named in the format
    "start_year/end_year+1".
    The command checks if each season is valid before creating it.
    After creating a season, it ensures that the `is_current`
    field has a determinate value (True or False).
    """

    help = "Adds seasons to the database based on the given start and end year."

    def add_arguments(self, parser: CommandParser) -> None:
        """Defines the command arguments."""
        parser.add_argument(
            "start_year", type=int, help="The start year for the season range."
        )
        parser.add_argument(
            "end_year", type=int, help="The end year for the season range."
        )

    def handle(self, *args, **kwargs):
        """Main logic for the command."""
        start_year: int = kwargs["start_year"]
        end_year: int = kwargs["end_year"]

        # Check if the provided years match the YYYY format using regex
        if not re.match(r"^\d{4}$", str(start_year)) or not re.match(
            r"^\d{4}$", str(end_year)
        ):
            raise CommandError(
                "Both start_year and end_year must be in the format YYYY (having 4 digits)."  # noqa: E501
            )
        # Ensure the provided start year is not greater than the end year.
        if start_year > end_year:
            raise CommandError("The start_year must be less than or equal to end_year.")

        # Loop through each year in the given range.
        for year in range(start_year, end_year + 1):
            season_name = f"{year}/{year + 1}"
            # Validate the season name format.
            if not services.SeasonService.is_valid(season_name):
                self.stdout.write(
                    self.style.ERROR(f"Season {season_name} is not valid. Skipping.")
                )
                continue
            # Fetch or create the season from the database.
            season = services.SeasonService.get(season_name)

            # Ensure the `is_current` field is not left null.
            if season.is_current is None:
                season.is_current = False

            # Save the season to the database.
            season.save()
            self.stdout.write(f"Processed season {season_name}.")

        self.stdout.write(self.style.SUCCESS("Seasons processed successfully!"))
