import logging

from django.core.management.base import BaseCommand

from profiles.services import PlayerPositionService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Player position management command."""

    help = (
        "Change player positions objects. "
        "This command should be run after the migration 0147_auto_20240102_1039.py."
    )

    def handle(self, *args, **options) -> None:
        """Handle the command."""
        position_service = PlayerPositionService()
        position_service.start_position_cleanup_process()
        position_service.update_score_for_position()
