import json

from celery import shared_task
from django.utils import timezone
from django_celery_beat.models import ClockedSchedule, PeriodicTask

from mailing.schemas import EmailTemplateRegistry
from mailing.services import MailingService
from mailing.utils import build_email_context
from profiles import models as profile_models
from profiles.services import NotificationService


@shared_task
def setup_premium_profile(
    profile_id: int, profile_class: str, premium_type: str, period: int = None
) -> None:
    model = getattr(profile_models, profile_class)
    profile = model.objects.get(pk=profile_id)

    premium_type = profile_models.PremiumType(premium_type)
    pp_object = profile.premium_products
    premium, _ = profile_models.PremiumProfile.objects.get_or_create(product=pp_object)

    if pp_object.trial_tested and premium_type == profile_models.PremiumType.TRIAL:
        raise ValueError("Trial already tested or cannot be set.")

    if premium_type == profile_models.PremiumType.CUSTOM and period:
        premium.setup_by_days(period)
    elif premium_type != profile_models.PremiumType.CUSTOM:
        premium.setup(premium_type)
    else:
        raise ValueError("Custom period requires period value.")

    if not pp_object.trial_tested:
        pp_object.trial_tested = True
        pp_object.save(update_fields=["trial_tested"])

    if premium.is_trial and premium_type != profile_models.PremiumType.TRIAL:
        pp_object.inquiries.reset_counter(reset_plan=False)


@shared_task
def post_create_profile_tasks(class_name: str, profile_id: int) -> None:
    """
    Create a profile for the user if it doesn't exist.
    """

    model = getattr(profile_models, class_name)
    profile: profile_models.BaseProfile = model.objects.get(pk=profile_id)

    profile.ensure_verification_stage_exist(commit=False)
    profile.ensure_premium_products_exist(commit=False)
    profile.ensure_visitation_exist(commit=False)
    profile.ensure_meta_exist(commit=False)
    profile.save()
    create_post_create_profile__periodic_tasks.delay(class_name, profile_id)
    NotificationService(profile.meta).notify_welcome()

    if profile.user.display_status == profile_models.User.DisplayStatus.NOT_SHOWN:
        NotificationService(profile.meta).notify_profile_hidden()


@shared_task
def check_profile_one_hour_after(profile_id: int, model_name: str) -> None:
    """
    Check if the profile is verified and notify the user.
    """
    model = getattr(profile_models, model_name)
    try:
        profile = model.objects.get(pk=profile_id)
    except model.DoesNotExist:
        return

    service = NotificationService(profile.meta)
    if profile:
        if not profile.team_history_object:
            service.notify_assign_club()

        if not profile.external_links.links.exists():
            service.notify_add_links()

        if not profile.user.user_video.exists():
            service.notify_add_video()


@shared_task
def check_profile_one_day_after(profile_id: int, model_name: str) -> None:
    """
    Check if the profile is verified and notify the user.
    """
    model = getattr(profile_models, model_name)
    try:
        profile = model.objects.get(pk=profile_id)
    except model.DoesNotExist:
        return

    service = NotificationService(profile.meta)

    if profile:
        if model_name == "PlayerProfile" and not profile.meta.transfer_status:
            service.notify_set_status()

        if (
            model_name in ["CoachProfile", "ClubProfile", "ManagerProfile"]
            and not profile.meta.transfer_requests
        ):
            service.notify_set_transfer_requests()

        if profile.products and not profile.products.trial_tested:
            service.notify_check_trial()


@shared_task
def check_profile_two_days_after(profile_id: int, model_name: str) -> None:
    """
    Check if the profile is verified and notify the user.
    """
    model = getattr(profile_models, model_name)
    try:
        profile = model.objects.get(pk=profile_id)
    except model.DoesNotExist:
        return

    service = NotificationService(profile.meta)

    if profile:
        service.notify_invite_friends()


@shared_task
def check_profile_four_days_after(profile_id: int, model_name: str) -> None:
    """
    Check if the profile is verified and notify the user.
    """
    model = getattr(profile_models, model_name)
    try:
        profile = model.objects.get(pk=profile_id)
    except model.DoesNotExist:
        return

    service = NotificationService(profile.meta)

    if profile:
        if not profile.is_premium:
            service.notify_go_premium()


@shared_task
def create_post_create_profile__periodic_tasks(
    model_name: str, profile_id: int
) -> None:
    """
    Create a profile for the user if it doesn't exist.
    """
    task_args = json.dumps([profile_id, model_name])

    PeriodicTask.objects.create(
        name=f"Run one hour after profile creation [ {profile_id} -- {model_name} ]",
        task="profiles.tasks.check_profile_one_hour_after",
        args=task_args,
        one_off=True,
        clocked=ClockedSchedule.objects.create(
            clocked_time=timezone.now() + timezone.timedelta(hours=1)
        ),
    )
    PeriodicTask.objects.create(
        name=f"Run one day after profile creation [ {profile_id} -- {model_name} ]",
        task="profiles.tasks.check_profile_one_day_after",
        args=task_args,
        one_off=True,
        clocked=ClockedSchedule.objects.create(
            clocked_time=timezone.now() + timezone.timedelta(days=1)
        ),
    )
    PeriodicTask.objects.create(
        name=f"Run two days after profile creation [ {profile_id} -- {model_name} ]",
        task="profiles.tasks.check_profile_two_days_after",
        args=task_args,
        one_off=True,
        clocked=ClockedSchedule.objects.create(
            clocked_time=timezone.now() + timezone.timedelta(days=2)
        ),
    )
    PeriodicTask.objects.create(
        name=f"Run four days after profile creation [ {profile_id} -- {model_name} ]",
        task="profiles.tasks.check_profile_four_days_after",
        args=task_args,
        one_off=True,
        clocked=ClockedSchedule.objects.create(
            clocked_time=timezone.now() + timezone.timedelta(days=4)
        ),
    )


@shared_task
def post_create_player_profile(pk: int) -> None:
    """
    Post-save signal handler for PlayerProfile to ensure metrics exist.
    """
    profile = profile_models.PlayerProfile.objects.get(pk=pk)
    context = build_email_context(profile.user)
    MailingService(EmailTemplateRegistry.PLAYER_WELCOME(context)).send_mail(
        profile.user
    )


@shared_task
def post_create_other_profile(pk: int, profile_class_name: str) -> None:
    """
    Post-save signal handler for ScoutProfile, CoachProfile, and ClubProfile.
    """
    if profile_class_name not in ["CoachProfile", "ClubProfile", "ScoutProfile"]:
        return

    profile_model = getattr(profile_models, profile_class_name)

    if profile := profile_model.objects.filter(pk=pk).first():
        context = build_email_context(profile.user)
        MailingService(EmailTemplateRegistry.PROFESSIONAL_WELCOME(context)).send_mail(
            profile.user
        )
