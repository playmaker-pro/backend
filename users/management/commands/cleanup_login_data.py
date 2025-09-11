import logging

from django.core.management.base import BaseCommand

from users.mongo_login_service import mongo_login_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clean up old user login data from MongoDB storage."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Number of days of recent login data to keep. Defaults to 30.",
        )

    def handle(self, *args, **options):
        days_to_keep = options["days"]
        self.stdout.write(
            self.style.SUCCESS(
                f"Starting cleanup of login data older than {days_to_keep} days..."
            )
        )

        try:
            success = mongo_login_service.cleanup_old_data(days_to_keep)

            if success:
                self.stdout.write(
                    self.style.SUCCESS("Successfully cleaned up old login data.")
                )
            else:
                self.stdout.write(
                    self.style.ERROR("Cleanup failed. Check logs for details.")
                )

        except Exception as e:
            logger.error(f"An unexpected error occurred during cleanup: {e}")
            self.stdout.write(self.style.ERROR(f"An unexpected error occurred: {e}"))
