import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from profiles.services import NotificationService
from profiles.tasks import (
    create_post_create_profile__periodic_tasks,
    post_create_other_profile,
    post_create_player_profile,
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
def post_save_player_profile(sender, instance, created, **kwargs):
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
        profile_class_name = instance.__class__.__name__
        instance.ensure_verification_stage_exist(commit=False)
        instance.ensure_visitation_exist(commit=False)
        instance.ensure_meta_exist(commit=False)
        instance.ensure_premium_products_exist(commit=False)
        instance.save()
        create_post_create_profile__periodic_tasks.delay(
            profile_class_name, instance.pk
        )
        NotificationService(instance.meta).notify_welcome()

        if instance.user.display_status == User.DisplayStatus.NOT_SHOWN:
            NotificationService(instance.meta).notify_profile_hidden()

        if profile_class_name in ["CoachProfile", "ClubProfile", "ScoutProfile"]:
            post_create_other_profile.delay(instance.pk, profile_class_name)
        elif profile_class_name == "PlayerProfile":
            post_create_player_profile.delay(instance.pk)


@receiver(post_save, sender=models.ProfileVisitation)
def post_profile_visitation(sender, instance, created, **kwargs):
    """
    Create a profile visitation for the user if it doesn't exist.
    """
    if created:
        NotificationService(instance.visited.profile.meta).notify_profile_visited()
