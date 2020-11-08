import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from notifications.mail import mail_role_change_request

from . import models


logger = logging.getLogger(__name__)


def set_and_create_user_profile(user):

    if user.declared_role == 'T':
        profile_model = models.CoachProfile
    elif user.declared_role == 'P':
        profile_model = models.PlayerProfile
    elif user.declared_role == 'C':
        profile_model = models.ClubProfile
    elif user.declared_role == 'G':
        profile_model = models.GuestProfile
    elif user.declared_role == 'S':
        profile_model = models.StandardProfile
    else:
        profile_model = models.StandardProfile

    profile_model.objects.get_or_create(user=user)
    # profile.save()


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile_handler(sender, instance, created, **kwargs):
    '''Signal reponsible for creating and attaching proper profile to user during creation process.

    Based on declared role append proper role (profile)
    '''
    if not created:  # this place is point where we decide if we wont to update user's profile each time.
        # mechanism to prevent double db queries would be to detect if role has been requested to update.
        msgprefix = 'Updated'
        set_and_create_user_profile(instance)

    msgprefix = 'New'
    set_and_create_user_profile(instance)

    logger.info(f"{msgprefix} user profile for {instance} created with declared role {instance.declared_role}")


@receiver(post_save, sender=models.RoleChangeRequest)
def change_profile_approved_handler(sender, instance, created, **kwargs):
    '''users.User.declared_role is central point to navigate with role changes.
    admin can alter somees role just changing User.declared_role
    '''
    if created:  # we assume that when object is created RoleChangedRequest only admin shold recieve notifiaction.
        mail_role_change_request(instance)
        return

    if instance.approved:
        user = instance.user
        user.declared_role = instance.new
        user.save()  # this should invoke create_profile_handler signal
        # set_and_create_user_profile(user)
        logger.info(f"User {user} profile changed to {instance.new} sucessfully due to: accepted RoleChangeRequest")
