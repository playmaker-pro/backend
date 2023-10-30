import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from inquiries.services import InquireService
from notifications.mail import mail_admins_about_new_user, mail_role_change_request

from . import models

logger = logging.getLogger(__name__)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile_handler(sender, instance, created, **kwargs):
    """Signal reponsible for creating and attaching proper profile to user during creation process.

    Based on declared role append proper role (profile)
    """
    inquire_service = InquireService()

    if (
        not created
    ):  # this place is point where we decide if we want to update user's profile each time.
        # mechanism to prevent double db queries would be to detect if role has been requested to update.
        msgprefix = "Updated"

    if created:
        logger.debug(f"Sending email to admins about new user {instance.username}")
        mail_admins_about_new_user(instance)
        msgprefix = "New"

    inquire_service.create_basic_inquiry_plan(instance)
    logger.info(
        f"{msgprefix} user: {instance}."
    )


@receiver(post_save, sender=models.RoleChangeRequest)
def change_profile_approved_handler(sender, instance, created, **kwargs):
    """users.User.declared_role is central point to navigate with role changes.
    admin can alter somees role just changing User.declared_role
    """
    if (
        created
    ):  # we assume that when object is created RoleChangedRequest only admin shold recieve notifiaction.
        mail_role_change_request(instance)
        return

    if instance.approved:
        user = instance.user
        user.declared_role = instance.new
        user.unverify(silent=True)
        user.save()  # this should invoke create_profile_handler signal
        # set_and_create_user_profile(user)
        logger.info(
            f"User {user} profile changed to {instance.new} sucessfully due to: accepted RoleChangeRequest"
        )
