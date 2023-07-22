import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications.mail import mail_admins_about_new_user, mail_role_change_request
from roles import definitions

from . import models, services

logger = logging.getLogger(__name__)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_and_attach_announcement_plans_handler(sender, instance, created, **kwargs):
    """Signal reponsible for creating and attaching proper profile to user during creation process.

    Based on declared role append proper role (profile)
    """
    service = services.MarketPlaceService()
    if created:
        service.set_user_plan(instance)
