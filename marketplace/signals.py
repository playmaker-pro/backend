import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from notifications.mail import mail_role_change_request, mail_admins_about_new_user
from roles import definitions
from . import models


logger = logging.getLogger(__name__)


def create_default_basic_plan_if_not_present():
    ''' In case when there is no Default plan we would like to create it at first time'''

    args = settings.ANNOUNCEMENT_INITAL_PLAN
    try:
        default = models.AnnouncementPlan.objects.get(default=True)
    except models.AnnouncementPlan.DoesNotExist:
        default = models.AnnouncementPlan.objects.create(**args)
    return default


def set_user_announcement_plan(user):
    try:
        models.AnnouncementUserQuota.objects.get(user=user)
    except models.AnnouncementUserQuota.DoesNotExist:
        default = create_default_basic_plan_if_not_present()
        models.AnnouncementUserQuota.objects.create(plan=default, user=user)
        logger.info(f'User {user.id} announcement plan created.')


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_and_attach_announcement_plans_handler(sender, instance, created, **kwargs):
    '''Signal reponsible for creating and attaching proper profile to user during creation process.

    Based on declared role append proper role (profile)
    '''
    if created:
        set_user_announcement_plan(instance)
