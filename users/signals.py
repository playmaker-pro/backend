import logging

from celery import chain
from django.contrib.auth import get_user_model, user_logged_in
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from mailing.tasks import notify_admins
from users.models import UserRef
from users.services import ReferralRewardService
from users.tasks import prepare_new_user, send_email_to_confirm_new_user

logger = logging.getLogger("project")
User = get_user_model()


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    breakpoint()
    logger.info(f"User '{user.username}' logged in ")


@receiver(pre_save, sender=User)
def pre_save_user(sender, instance, **kwargs):
    if instance.first_name == instance.last_name:
        instance.display_status = User.DisplayStatus.NOT_SHOWN


@receiver(post_save, sender=User)
def post_create_user(sender, instance, created, **kwargs) -> None:
    """Create UserPreferences object for each new user"""
    if created:
        chain(
            prepare_new_user.s(user_id=instance.pk),
            send_email_to_confirm_new_user.s(user_id=instance.pk),
        ).apply_async()


@receiver(post_save, sender=UserRef)
def referral_rewards(sender, instance, created, **kwargs) -> None:
    if created:
        referral = instance.ref_by
        invited_users = referral.registered_users.count()

        if invited_users > 0 and invited_users % 10 == 0:
            subject = f"Osiągnięto {invited_users} poleconych użytkowników przez {str(referral)}."
            message = (
                f"Link afiliacyjny {referral} osiągnął {invited_users} poleconych."
            )
            notify_admins.delay(subject, message)

        if referral.is_user:
            ReferralRewardService(referral.user).check_and_reward()
