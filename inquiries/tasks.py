from celery import shared_task
from celery.utils.log import get_task_logger

from inquiries.constants import INQUIRY_EMAIL_TEMPLATE, InquiryLogType
from inquiries.models import InquiryRequest, UserInquiry, UserInquiryLog
from mailing.schemas import EmailTemplateRegistry, Envelope
from mailing.services import MailingService
from mailing.utils import build_email_context
from utils.constants import INQUIRY_LIMIT_INCREASE_URL

logger = get_task_logger(__name__)


@shared_task
def notify_limit_reached(user_inquiry_id: int):
    """
    Notify the user that they have reached their inquiry limit.
    This task can be scheduled to run periodically to check user limits.
    """
    user_inquiry = UserInquiry.objects.get(pk=user_inquiry_id)

    if not user_inquiry.can_sent_inquiry_limit_reached_email():
        return

    MailingService(
        EmailTemplateRegistry.INQUIRY_LIMIT(context={"url": INQUIRY_LIMIT_INCREASE_URL})
    ).send_mail(user_inquiry.user)
    user_inquiry.update_last_limit_notification()


@shared_task
def send_inquiry_update_email(user_inquiry_log_id: int):
    """
    Send an email notification when a user inquiry is updated.
    This task is triggered by the post_save signal of UserInquiryLog.
    """
    user_inquiry_log = UserInquiryLog.objects.get(pk=user_inquiry_log_id)
    gender_index = int(user_inquiry_log.related_with.user.userpreferences.gender == "K")

    context = build_email_context(
        user=(user := user_inquiry_log.log_owner.user),
        user2=user_inquiry_log.related_with.user,
    )
    if user_inquiry_log.log_type == InquiryLogType.ACCEPTED:
        context.update({"verb": ["zaakceptował", "zaakceptowała"][gender_index]})
    elif user_inquiry_log.log_type == InquiryLogType.REJECTED:
        context.update({"verb": ["odrzucił", "odrzuciła"][gender_index]})

    try:
        template = INQUIRY_EMAIL_TEMPLATE[user_inquiry_log.log_type]
    except KeyError as e:
        logger.error(
            f"Email template for log type {user_inquiry_log.log_type} not found: {e}"
        )
        return

    envelope = Envelope(mail=template(context), recipients=[user.email])
    envelope.send()


@shared_task
def check_inquiry_response(inquiry_request_id: int):
    """
    Check if an inquiry request has been responded to within 7 days.
    This task can be scheduled to run periodically to check for responses.
    """
    inquiry_request = InquiryRequest.objects.get(pk=inquiry_request_id)

    if inquiry_request.status not in InquiryRequest.RESOLVED_STATES:
        mail_schema = EmailTemplateRegistry.OUTDATED_REMINDER
        context = build_email_context(
            user=inquiry_request.sender.user,
            user2=inquiry_request.recipient.user,
        )
        MailingService(mail_schema(context)).send_mail(inquiry_request.sender)
