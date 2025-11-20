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
        Each step is isolated with its own try/except; on failure we notify admins
        but continue with the remaining steps.
        """
        logger.info("Starting daily mailings")
        postman = PostmanService()

        # 1) Incomplete profiles
        try:
            postman.blank_profile()
        except Exception as e:
            logger.error("Postman step blank_profile failed: %s", e, exc_info=True)

        # 2) Inactive 30 days
        try:
            postman.inactive_for_30_days()
        except Exception as e:
            logger.error(
                "Postman step inactive_for_30_days failed: %s", e, exc_info=True
            )

        # 3) Inactive 90 days
        try:
            postman.inactive_for_90_days()
        except Exception as e:
            logger.error(
                "Postman step inactive_for_90_days failed: %s", e, exc_info=True
            )

        # 4) Go premium encouragements
        try:
            postman.go_premium()
        except Exception as e:
            logger.error("Postman step go_premium failed: %s", e, exc_info=True)

        # 5) Invite friends
        try:
            postman.invite_friends()
        except Exception as e:
            logger.error("Postman step invite_friends failed: %s", e, exc_info=True)

        # 6) Views monthly milestone
        try:
            postman.views_monthly()
        except Exception as e:
            logger.error("Postman step views_monthly failed: %s", e, exc_info=True)

        # 7) Player without transfer status
        try:
            postman.player_without_transfer_status()
        except Exception as e:
            logger.error(
                "Postman step player_without_transfer_status failed: %s",
                e,
                exc_info=True,
            )

        # 8) Profile without transfer request
        try:
            postman.profile_without_transfer_request()
        except Exception as e:
            logger.error(
                "Postman step profile_without_transfer_request failed: %s",
                e,
                exc_info=True,
            )

        logger.info("Daily mailings finished (with per-step error handling)")
