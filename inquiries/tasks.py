from celery import shared_task


@shared_task
def send_inquiry_email(*args, **kwargs) -> None:
    from inquiries.models import UserInquiryLog

    breakpoint()
    log_id = kwargs.get("log_id")
    log = UserInquiryLog.objects.get(pk=log_id)
    log.send_email_to_user()
