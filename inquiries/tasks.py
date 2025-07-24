from celery import shared_task

from inquiries.models import UserInquiry
from mailing.schemas import EmailTemplateRegistry
from mailing.services import MailingService
from utils.constants import INQUIRY_LIMIT_INCREASE_URL


@shared_task
def notify_limit_reached(user_inquiry_id: int):
    """
    Notify the user that they have reached their inquiry limit.
    This task can be scheduled to run periodically to check user limits.
    """

    user_inquiry = UserInquiry.objects.get(pk=user_inquiry_id)

    MailingService(
        EmailTemplateRegistry.INQUIRY_LIMIT(context={"url": INQUIRY_LIMIT_INCREASE_URL})
    ).send_mail(user_inquiry.user)

    user_inquiry.update_last_limit_notification()
