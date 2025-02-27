import logging

from celery import chain
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from mailing.tasks import notify_admins
from premium.tasks import reward_referrals_with_premium
from users.models import UserRef
from users.tasks import prepare_new_user, send_email_to_confirm_new_user

logger = logging.getLogger("project")
User = get_user_model()


@receiver(pre_save, sender=User)
def pre_save_user(sender, instance, **kwargs):
    # This is mechanism to overwrite username for each account. s
    instance.username = instance.email


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
    """Create UserPreferences object for each new user"""
    if created:
        referral = instance.ref_by
        invited_users = referral.registered_users.count()

        if invited_users > 0 and invited_users % 10 == 0:
            pp = None
            if (
                referral.user
                and referral.user.profile
                and referral.user.profile.premium_products
            ):
                pp = referral.user.profile.premium_products
                reward_referrals_with_premium.delay(premium_products_id=pp.pk)

            subject = f"Osiągnięto {invited_users} poleconych użytkowników przez {str(referral)}."
            message = (
                f"Link afiliacyjny {referral} osiągnął {invited_users} poleconych.\n"
            )

            if pp:
                message += f"Użytkownikowi {pp.profile} zostało aktywowane/przedłużone premium o 10 dni."
            elif referral.user:
                message += (
                    f"Niestety, nie udało się aktywować premium dla {referral.user}."
                )

            notify_admins.delay(subject, message)
