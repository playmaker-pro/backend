"""
Module containing Celery tasks for notifications in PlayMaker.
"""

from celery import shared_task
from django.conf import settings
from django.core.files import File

from notifications.models import Notification


@shared_task
def create_notification(
    **kwargs,
) -> None:
    """
    Create notification for profile based on provided kwargs.
    If picture path is provided, it will be used to set the picture field.
    If the notification already exists, it will be refreshed.
    """

    if picture_path := kwargs.get("picture", None):
        full_path = settings.MEDIA_ROOT / picture_path
        if full_path.exists():
            with open(full_path, "rb") as file:
                picture = File(file)
                kwargs["picture"] = picture

    notification, created = Notification.objects.get_or_create(
        target_id=kwargs.pop("profile_meta_id"),
        title=kwargs.pop("title"),
        description=kwargs.pop("description"),
        href=kwargs.pop("href"),
        defaults=kwargs,
    )

    if not created:
        notification.refresh()
