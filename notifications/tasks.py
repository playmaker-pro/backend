from celery import shared_task

from notifications.models import Notification


@shared_task
def create_notification(*args, **kwargs) -> Notification:
    return Notification.objects.create(*args, **kwargs)
