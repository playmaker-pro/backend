import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from notifications.mail import mail_role_change_request
from users.models import User

from . import models

logger = logging.getLogger(__name__)


@receiver(post_save, sender=models.RoleChangeRequest)
def change_profile_approved_handler(sender, instance, created, **kwargs):
    """users.User.declared_role is central point to navigate with role changes.
    admin can alter somees role just changing User.declared_role
    """
    # we assume that when object is created RoleChangedRequest only admin
    # should receive notification.
    if created:
        mail_role_change_request(instance)
        return

    if instance.approved:
        user = instance.user
        user.declared_role = instance.new
        user.unverify(silent=True)
        user.save()  # this should invoke create_profile_handler signal
        # set_and_create_user_profile(user)
        logger.info(
            f"User {user} profile changed to {instance.new} "
            f"sucessfully due to: accepted RoleChangeRequest"
        )


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
