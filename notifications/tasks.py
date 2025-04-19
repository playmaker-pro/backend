from celery import shared_task

from notifications.models import Notification


@shared_task
def create_notification(
    profile_meta_id: int, title: str, description: str, href: str, template_name: str
) -> None:
    notification, created = Notification.objects.get_or_create(
        profile_id=profile_meta_id,
        title=title,
        description=description,
        href=href,
        template_name=template_name,
    )

    if not created:
        notification.refresh()
