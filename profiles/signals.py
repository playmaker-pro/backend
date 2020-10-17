import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from . import models


logger = logging.getLogger(__name__)


def set_and_create_user_profile(user):

    if user.declared_role == 'T':
        profile = models.CoachProfile(user=user)
    elif user.declared_role == 'P':
        profile = models.PlayerProfile(user=user)
    elif user.declared_role == 'C':
        profile = models.ClubProfile(user=user)
    else:
        profile = models.StandardProfile(user=user)
    profile.save()

    user.current_profile = profile


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
    if created:  # we assume that when object is created RoleChangedRequest only admin shold recieve notifiaction.
        return  # @todo add admin notification here in case of new change request....

    if instance.approved:
        if instance.new == 'player':  # @todo - for sure this need to be unified (one source of names.... )
            profile = models.PlayerProfile(user=instance.user)
        elif instance.new == 'coach':  # @todo - for sure this need to be unified (one source of names.... )
            profile = models.CoachProfile(user=instance.user)
            # @todo add more variants to addd (maybe more generic way)
        profile.save()
        #  @todo - reattach current_profile to user account
        logger.info(f"User {instance.user} profile changed to {instance.new} sucessfully")
