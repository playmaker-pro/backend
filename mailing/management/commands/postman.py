import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from mailing.services import PostmanService

logger = logging.getLogger("commands")

User = get_user_model()


class Command(BaseCommand):
    help = "Daily mailings"

    def handle(self, *args, **options):
        """
        Handle the command to run daily mailings.
        This includes checking for profiles that need attention.
        """
        try:
            logger.info("Starting daily mailings")
            postman = PostmanService()
            postman.blank_profile()
            postman.inactive_for_30_days()
            postman.inactive_for_90_days()
            postman.go_premium()
            postman.invite_friends()
            postman.views_monthly()
            postman.player_without_transfer_status()
            postman.profile_without_transfer_request()

            logger.info("Daily mailings completed successfully")
        except Exception as e:
            logger.error(f"Postman failed: {e}", exc_info=True)
            raise  # Re-raise to trigger admin notification
