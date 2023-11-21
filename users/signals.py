import logging

# from allauth.account.signals import email_confirmed
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from users.models import UserPreferences
from users.services import UserService

logger = logging.getLogger("project")


User = get_user_model()

# TODO(rkesik): deprecated - do wywalenia - zostawiamy do konca budowy API pod FE
# @receiver(email_confirmed)
# def email_confirmed_(request, email_address, **kwargs):
#     '''Set User.state to email verified'''
#     user = User.objects.get(email=email_address.email)
#     user.verify_email()
#     user.save()


@receiver(pre_save, sender=settings.AUTH_USER_MODEL)
def pre_save_user(sender, instance, **kwargs):
    # This is mechanism to overwrite username for each account. s
    instance.username = instance.email


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def post_create_user(sender, instance, created, **kwargs) -> None:
    """Create UserPreferences object for each new user"""
    if created:
        UserPreferences.objects.get_or_create(user=instance)
        UserService.send_email_to_confirm_new_user(instance)
