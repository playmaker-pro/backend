import logging

from django.contrib.auth import user_logged_in
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from inquiries.services import InquireService
from mailing.models import Mailing
from mailing.tasks import notify_admins
from users.models import Ref, User, UserPreferences, UserRef
from users.services import ReferralRewardService, UserService
from users.tasks import send_email_to_confirm_new_user

logger = logging.getLogger("project")


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    logger.info(f"User '{user.username}' logged in ")


@receiver(pre_save, sender=User)
def pre_save_user(sender, instance, **kwargs):
    if instance.first_name == instance.last_name:
        instance.display_status = User.DisplayStatus.NOT_SHOWN


@receiver(post_save, sender=User)
def post_save_user(sender, instance, created, **kwargs) -> None:
    """Create UserPreferences object for each new user"""
    if created:
        UserPreferences.objects.get_or_create(user=instance)
        Ref.objects.get_or_create(user=instance)
        InquireService.create_basic_inquiry_plan(instance)
        Mailing.objects.get_or_create(user=instance)
        (send_email_to_confirm_new_user.delay(user_id=instance.pk),)
    else:
        old_object = User.objects.get(pk=instance.pk)

        if old_object.email != instance.email:
            instance.is_email_verified = False
            UserService.send_email_to_confirm_new_email_address(instance)


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
            notify_admins.delay(subject=subject, message=message)

        if referral.is_user:
            ReferralRewardService(referral.user).check_and_reward()
