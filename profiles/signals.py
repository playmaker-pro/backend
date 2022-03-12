import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from notifications.mail import mail_role_change_request, mail_admins_about_new_user
from roles import definitions
from . import models
from .services import ProfileService


logger = logging.getLogger(__name__)


# @todo this shoudl be moved to another place (inquires)
from inquiries.models import UserInquiry
from inquiries.models import InquiryPlan


def create_default_basic_plan_if_not_present():
    ''' In case when there is no Default plan we would like to create it at first time'''

    args = settings.INQUIRIES_INITAL_PLAN
    try:
        default = InquiryPlan.objects.get(default=True)
    except InquiryPlan.DoesNotExist:
        default = InquiryPlan.objects.create(**args)
    return default


def create_default_basic_plan_for_coach_if_not_present():
    args = settings.INQUIRIES_INITAL_PLAN_COACH
    try:
        plan = InquiryPlan.objects.get(name=args['name'])

    except InquiryPlan.DoesNotExist:
        logger.info('Initial InquiryPlan for coaches does not exists. Creating new one.')
        plan = InquiryPlan.objects.create(**args)
    return plan


def set_user_inquiry_plan(user):
    try:
        UserInquiry.objects.get(user=user)
    except UserInquiry.DoesNotExist:
        if user.is_coach or user.is_club:
            default = create_default_basic_plan_for_coach_if_not_present()
        else:
            default = create_default_basic_plan_if_not_present()
        UserInquiry.objects.create(plan=default, user=user)
        logger.info(f'User {user.id} plan created.')


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile_handler(sender, instance, created, **kwargs):
    '''Signal reponsible for creating and attaching proper profile to user during creation process.

    Based on declared role append proper role (profile)
    '''
    service = ProfileService()

    if not created:  # this place is point where we decide if we want to update user's profile each time.
        # mechanism to prevent double db queries would be to detect if role has been requested to update.
        msgprefix = 'Updated'
        profile = service.set_and_create_user_profile(instance)
        service.set_initial_verification(profile)

    if created:
        logger.debug(f'Sending email to admins about new user {instance.username}')
        mail_admins_about_new_user(instance)
        msgprefix = 'New'

    # @todo(rkesik): that second call of set_and_create_user_profile might be not needed.
    service.set_and_create_user_profile(instance)
    set_user_inquiry_plan(instance)

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
        user.unverify(silent=True)
        user.save()  # this should invoke create_profile_handler signal
        # set_and_create_user_profile(user)
        logger.info(f"User {user} profile changed to {instance.new} sucessfully due to: accepted RoleChangeRequest")
