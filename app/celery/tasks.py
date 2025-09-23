from logging import getLogger

from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.management import call_command
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from profiles.services import NotificationService

logger = get_task_logger(__name__)


logger = getLogger("celery")


@shared_task
def notify_check_trial() -> None:
    """
    Send notifications to users about trial expiration.
    """
    NotificationService.notify_check_trial()


@shared_task
def notify_verify_profile() -> None:
    """
    Send notifications to users to verify their profile every two days.
    """
    NotificationService.notify_verify_profile()


@shared_task
def notify_pm_rank() -> None:
    """
    Send weekly notifications to users about PM rank updates.
    """
    NotificationService.notify_pm_rank()


@shared_task
def notify_visits_summary() -> None:
    """
    Send notifications to users summarizing profile visits every month.
    """
    NotificationService.notify_visits_summary()


@shared_task
def notify_set_transfer_request() -> None:
    """
    Send notifications to users to set transfer requests every month
    """
    NotificationService.notify_set_transfer_requests()


@shared_task
def notify_set_status() -> None:
    """
    Send notifications to users to set their transfer status every month.
    """
    NotificationService.notify_set_status()


@shared_task
def notify_add_links() -> None:
    """
    Send notifications to users to add links to their profile every month.
    """
    NotificationService.notify_add_links()


@shared_task
def notify_add_video() -> None:
    """
    Send notifications to users to add videos to their profile every month.
    """
    NotificationService.notify_add_video()


@shared_task
def notify_invite_friends() -> None:
    """
    Send weekly notifications to users to invite friends once a week.
    """
    NotificationService.notify_invite_friends()


@shared_task
def notify_profile_hidden() -> None:
    """
    Send notifications to users about their profile being hidden every two days.
    """
    NotificationService.notify_profile_hidden()


@shared_task
def notify_assign_club() -> None:
    """
    Send notifications to users to assign their current club every month.
    """
    NotificationService.notify_assign_club()


@shared_task  # TODO: remove this task
def notify_as_test_each_minute() -> None:
    """
    Test task to check profile hidden status every minute.
    """
    NotificationService.bulk_notify_test()


NOTIFICATIONS = [
    {
        "name": "Notify to check trial premium",
        "task": "app.celery.tasks.bulk_notify_check_trial",
        "schedule": CrontabSchedule.objects.get_or_create(
            minute=0, hour=2, day_of_month=2
        ),
        "enabled": True,
    },
    {
        "name": "Notify to verify profile",
        "task": "app.celery.tasks.bulk_notify_verify_profile",
        "schedule": CrontabSchedule.objects.get_or_create(
            minute=0, hour=4, day_of_month=20
        ),
        "enabled": True,
    },
    {
        "name": "Notify to check PM rank",
        "task": "app.celery.tasks.bulk_notify_pm_rank",
        "schedule": CrontabSchedule.objects.get_or_create(
            minute=0, hour=3, day_of_month=5
        ),
        "enabled": True,
    },
    {
        "name": "Notify to check visits summary",
        "task": "app.celery.tasks.bulk_notify_visits_summary",
        "schedule": CrontabSchedule.objects.get_or_create(
            minute=0, hour=1, day_of_month=15
        ),
        "enabled": True,
    },
    {
        "name": "Notify to set transfer request",
        "task": "app.celery.tasks.bulk_notify_set_transfer_request",
        "schedule": CrontabSchedule.objects.get_or_create(
            minute=0, hour=2, day_of_week=3
        ),
        "enabled": True,
    },
    {
        "name": "Notify to set status",
        "task": "app.celery.tasks.bulk_notify_set_status",
        "schedule": CrontabSchedule.objects.get_or_create(
            minute=0, hour=3, day_of_week=5
        ),
        "enabled": True,
    },
    {
        "name": "Notify to add links",
        "task": "app.celery.tasks.bulk_notify_add_links",
        "schedule": CrontabSchedule.objects.get_or_create(
            minute=0, hour=4, day_of_week=3
        ),
        "enabled": True,
    },
    {
        "name": "Notify to add video",
        "task": "app.celery.tasks.bulk_notify_add_video",
        "schedule": CrontabSchedule.objects.get_or_create(
            minute=0, hour=5, day_of_month=30
        ),
        "enabled": True,
    },
    {
        "name": "Notify to set transfer requests",
        "task": "app.celery.tasks.bulk_notify_set_transfer_requests",
        "schedule": CrontabSchedule.objects.get_or_create(
            minute=0, hour=3, day_of_month=30
        ),
        "enabled": True,
    },
    {
        "name": "Notify to invite friends",
        "task": "app.celery.tasks.bulk_notify_invite_friends",
        "schedule": CrontabSchedule.objects.get_or_create(
            minute=0, hour=1, day_of_week=3
        ),
        "enabled": True,
    },
    {
        "name": "Notify to profile hidden",
        "task": "app.celery.tasks.bulk_notify_profile_hidden",
        "schedule": CrontabSchedule.objects.get_or_create(
            minute=0, hour=4, day_of_month="*/2"
        ),
        "enabled": True,
    },
    {
        "name": "Notify to assign club",
        "task": "app.celery.tasks.bulk_notify_assign_club",
        "schedule": CrontabSchedule.objects.get_or_create(
            minute=0, hour=2, day_of_month=11
        ),
        "enabled": True,
    },
    {
        "name": "Test beat each minute",
        "task": "app.celery.tasks.notify_as_test_each_minute",
        "schedule": CrontabSchedule.objects.get_or_create(
            minute="*", hour="*", day_of_month="*", month_of_year="*", day_of_week="*"
        ),
        "enabled": False,
    },
]


def refresh_periodic_tasks() -> None:
    """
    Refresh periodic tasks in the database.
    """
    if to_delete := PeriodicTask.objects.filter(
        description="GENERIC_PERIODIC_TASK"
    ).exclude(task__in=[n["task"] for n in NOTIFICATIONS]):
        logger.info(
            f"Deleting {to_delete.count()} periodic tasks: {to_delete.values_list('name', flat=True)}"
        )
        to_delete.delete()

    for notification in NOTIFICATIONS:
        _, created = PeriodicTask.objects.update_or_create(
            name=notification["name"],
            task=notification["task"],
            defaults={
                "crontab": notification["schedule"][0],
                "enabled": notification["enabled"],
                "description": "GENERIC_PERIODIC_TASK",
            },
        )
        if created:
            logger.info(f"Created new periodic task: {notification['name']}")


@shared_task
def run_daily_supervisor() -> None:
    """
    Run the daily supervisor command to handle daily tasks.
    """

    call_command("daily_supervisor")
