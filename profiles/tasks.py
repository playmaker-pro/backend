import json

from celery import shared_task
from django.utils import timezone
from django_celery_beat.models import ClockedSchedule, PeriodicTask

from notifications.services import NotificationService
from profiles import models


@shared_task
def post_create_profile_tasks(class_name: str, profile_id: int) -> None:
    """
    Create a profile for the user if it doesn't exist.
    """

    model = getattr(models, class_name)
    profile: models.BaseProfile = model.objects.get(pk=profile_id)

    profile.ensure_verification_stage_exist(commit=False)
    profile.ensure_premium_products_exist(commit=False)
    profile.ensure_visitation_exist(commit=False)
    profile.ensure_meta_exist(commit=False)
    profile.save()
    create_post_create_profile__periodic_tasks(class_name, profile_id)
    NotificationService(profile.meta).notify_welcome()


@shared_task
def check_profile_one_hour_after(profile_id: int, model_name: str) -> None:
    """
    Check if the profile is verified and notify the user.
    """
    model = getattr(models, model_name)
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
    model = getattr(models, model_name)
    try:
        profile = model.objects.get(pk=profile_id)
    except model.DoesNotExist:
        return

    service = NotificationService(profile.meta)

    if profile:
        if (
            model_name == "PlayerProfile"
            and not profile.transfer_status_related.exists()
        ):
            service.notify_set_status()

        if (
            model_name in ["CoachProfile", "ClubProfile", "ManagerProfile"]
            and not profile.transfer_requests.exists()
        ):
            service.notify_set_transfer_requests()

        if profile.products and not profile.products.trial_tested:
            service.notify_check_trial()


@shared_task
def check_profile_two_days_after(profile_id: int, model_name: str) -> None:
    """
    Check if the profile is verified and notify the user.
    """
    model = getattr(models, model_name)
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
    model = getattr(models, model_name)
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
