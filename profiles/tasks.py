from celery import shared_task

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
    NotificationService(profile.meta).notify_welcome()
