import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from . import models

logger = logging.getLogger("project")


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile_handler(sender, instance, created, **kwargs):
    if not created:
        return
    # Create the profile object, only if it is newly created
    print('aaaaaaa:::::', instance.declared_role)
    if instance.declared_role == 'T':
        profile = models.CoachProfile(user=instance)
    elif instance.declared_role == 'P':
        profile = models.PlayerProfile(user=instance)
    
    # @todo add more variants
    else:    
        profile = models.Profile(user=instance)
    profile.save()
    
    logger.info("New user profile for {} created".format(instance))


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
