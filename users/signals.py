import logging

from allauth.account.signals import email_confirmed
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save
from django.dispatch import receiver
from . import models

logger = logging.getLogger("project")


User = get_user_model()


@receiver(email_confirmed)
def email_confirmed_(request, email_address, **kwargs):
    '''Set User.state to email verified'''
    user = User.objects.get(email=email_address.email)
    user.verify_email()
    user.save()


@receiver(pre_save, sender=models.UserVerification)
def user_verification(sender, instance, **kwargs):
    logger.info('User verification made.')


@receiver(pre_save, sender=settings.AUTH_USER_MODEL)
def update_username_from_email(sender, instance, **kwargs):
    # This is mechanism to overwrite username for each account. s
    instance.username = instance.email
