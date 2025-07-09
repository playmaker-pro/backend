import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from notifications.services import NotificationService
from profiles.tasks import (
    post_create_profile_tasks,
)
from users.models import User

from . import models

logger = logging.getLogger(__name__)


@receiver(post_save, sender=models.ProfileVisitation)
def enforce_visitation_limit(sender, instance, created, **kwargs):
    """
    Delete visitations older than 30 days to prevent the database from growing.
    """
    if created:
        cutoff_date = timezone.now() - timezone.timedelta(days=31)

        old_visitations = models.ProfileVisitation.objects.filter(
            visited=instance.visited, timestamp__lt=cutoff_date
        )
        old_visitations.delete()


@receiver(post_save, sender=models.PlayerProfile)
def ensure_metrics_exist(sender, instance, created, **kwargs):
    """
    Create metrics for a player profile if they don't exist.
    """
    if not hasattr(instance, "playermetrics"):
        models.PlayerMetrics.objects.get_or_create(player=instance)


@receiver(post_save, sender=models.PlayerMetrics)
def update_calculate_pm_score_product(sender, instance, **kwargs):
    pp = instance.player.premium_products
    if pp and hasattr(pp, "calculate_pm_score"):
        pp.calculate_pm_score.approve(User.get_system_user(), instance.pm_score)


@receiver(post_save, sender=models.PlayerProfile)
@receiver(post_save, sender=models.CoachProfile)
@receiver(post_save, sender=models.ClubProfile)
@receiver(post_save, sender=models.ManagerProfile)
@receiver(post_save, sender=models.ScoutProfile)
@receiver(post_save, sender=models.GuestProfile)
def post_create_profile(sender, instance, created, **kwargs):
    """
    Create a profile for the user if it doesn't exist.
    """
    if created:
        post_create_profile_tasks.delay(instance.__class__.__name__, instance.pk)


@receiver(post_save, sender=models.ProfileVisitation)
def post_profile_visitation(sender, instance, created, **kwargs):
    """
    Create a profile visitation for the user if it doesn't exist.
    """
    if created:
        NotificationService(instance.visited.profile.meta).notify_profile_visited()
