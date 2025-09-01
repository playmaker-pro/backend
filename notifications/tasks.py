"""
Module containing Celery tasks for notifications in PlayMaker.
"""

import os

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
        full_path = os.path.join(settings.MEDIA_URL, picture_path).split(
            settings.BASE_DIR
        )[-1]
        try:
            with open(full_path, "rb") as file:
                picture = File(file)
                kwargs["picture"] = picture
        except FileNotFoundError:
            pass

    profile_meta_id = kwargs.pop("profile_meta_id")
    title = kwargs.pop("title")
    description = kwargs.pop("description")
    href = kwargs.pop("href")
    template_name = kwargs.pop("template_name", None)
    template_params = kwargs.pop("template_params", None)


    notification, created = Notification.objects.get_or_create(
        target_id=profile_meta_id,
        title=title,
        description=description,
        href=href,
        defaults={
            "template_name": template_name,
            "template_params": template_params,
            **kwargs
        },
    )

    if not created:
        # Update existing notification with new template data
        notification.template_name = template_name
        notification.template_params = template_params
        notification.refresh()
