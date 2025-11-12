import uuid

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import get_connection, mail_admins, send_mail
from django.utils import timezone

from utils.functions import Timer

User = get_user_model()
logger = get_task_logger("mailing")
connection = get_connection()


@shared_task(bind=True, max_retries=3)
def notify_admins(subject: str, message: str, **kwargs):
    """Send notification to admins with error tracking."""
    if cache.get(subject):
        logger.info(f"Skipping duplicate admin notification: {subject}")
        return

    try:
        mail_admins(subject=subject, message=message, connection=connection)
        logger.info(f"Admin notification sent: {subject}")
        cache.set(subject, message, 3600)
    except Exception as err:
        logger.error(f"Admin notification failed: {err}")
        raise


@shared_task(bind=True, max_retries=3)
def send(
    self,
    operation_id: uuid.UUID,
    **data,
) -> None:
    """
    Enhanced email sending with metrics and better error handling.
    """
    from mailing.models import MailLog

    recipients = data.get("recipient_list", [])
    subject = data.get("subject")
    template_file = data.pop("template_file", None)

    if not recipients:
        logger.warning(f"[{operation_id}] No recipients provided")
        return {"status": "skipped", "reason": "no_recipients"}

    if not subject:
        logger.warning(f"[{operation_id}] No subject provided")

    try:
        for recipient in recipients:
            if user := User.objects.filter(email=recipient).first():
                mail_log, created = MailLog.objects.get_or_create(
                    mailing=user.mailing,
                    subject=subject,
                    created_at__gte=timezone.now()
                    - timezone.timedelta(minutes=15),  # antispam
                    defaults={
                        "mailing": user.mailing,
                        "mail_template": template_file,
                        "operation_id": operation_id,
                        "subject": subject,
                    },
                )
                if not created:
                    logger.info(
                        f"[{operation_id}] Antispam skip: {recipient} -- {subject}"
                    )
                    continue
            else:
                logger.warning(
                    f"[{operation_id}] No mailing found for recipient: {recipient}"
                )
                mail_log = None

            metadata = {}

            with Timer() as timer:
                try:
                    individual_data = data.copy()
                    individual_data["recipient_list"] = [recipient]
                    send_mail(
                        **individual_data,
                        fail_silently=False,
                        connection=connection,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                    )
                except Exception as err:
                    logger.error(
                        f"[{operation_id}] Failed to send email to {recipient}: {str(err)}"
                    )
                    metadata["error"] = str(err)
                    status = MailLog.MailStatus.FAILED
                else:
                    status = MailLog.MailStatus.SENT
                    logger.info(
                        f"[{operation_id}] Email sent to {recipient}: {subject[:50]}"
                    )
                finally:
                    metadata.update({
                        "duration_seconds": timer.duration,
                        "start_time": timer.start_time,
                        "end_time": timer.end_time,
                    })
                    if mail_log:
                        mail_log.update_metadata(metadata, status)

    except Exception as err:
        error_result = {
            "status": "failed",
            "error": str(err),
            "recipients_count": len(recipients),
            "operation_id": str(operation_id),
            **data,
        }
        logger.error(f"✗ Email failed: {error_result}")

        raise Exception(error_result) from err
