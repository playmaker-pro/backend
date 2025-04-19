from celery import shared_task


@shared_task
def notifications_once_a_month():
    """
    Send monthly notifications to users.
    """
    # Logic to send notifications
    pass


@shared_task
def notifications_once_a_week():
    """
    Send weekly notifications to users.
    """
    # Logic to send notifications
    pass
