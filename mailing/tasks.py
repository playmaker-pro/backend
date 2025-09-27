import time
import uuid

from celery import shared_task
from celery.utils.log import get_task_logger
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import mail_admins, send_mail

User = get_user_model()
logger = get_task_logger(__name__)


@shared_task
def notify_admins(subject: str, message: str, **kwargs):
    """Send notification to admins with error tracking."""
    if cache.get(subject):
        logger.info(f"Skipping duplicate admin notification: {subject}")
        return

    try:
        mail_admins(subject=subject, message=message, **kwargs)
        logger.info(f"Admin notification sent: {subject}")
        cache.set(subject, message, 3600)
    except Exception as err:
        logger.error(f"Admin notification failed: {err}")
        raise


@shared_task(bind=True, max_retries=3)
def send(self, separate: bool = False, track_metrics: bool = True, **data):
    """
    Enhanced email sending with metrics and better error handling.
    """
    from mailing.models import MailLog

    recipients = data.get("recipient_list", [])
    subject = data.get("subject", "No subject")
    start_time = time.time()
    operation_id = uuid.uuid4()
    template_file = data.pop("template_file", None)
    logger.info(f"[{operation_id}] Sending email to {len(recipients)} recipients")

    # Input validation
    if not recipients:
        logger.warning(f"[{operation_id}] No recipients provided")
        return {"status": "skipped", "reason": "no_recipients"}

    if not subject or subject == "No subject":
        logger.warning(f"[{operation_id}] No subject provided")

    users = User.objects.filter(email__in=recipients)
    for user in users:
        MailLog.objects.create(
            mailing=user.mailing,
            mail_template=template_file,
            operation_id=operation_id,
            subject=subject,
        )

    mail_logs = MailLog.objects.filter(operation_id=operation_id)

    try:
        if separate:
            for recipient in recipients:
                try:
                    individual_data = data.copy()
                    individual_data["recipient_list"] = [recipient]
                    send_mail(**individual_data, fail_silently=False)
                    metadata, status = (
                        {
                            "recipients_count": len(recipients),
                            "duration_seconds": round(time.time() - start_time, 3),
                            "subject": subject,
                        },
                        MailLog.MailStatus.SENT,
                    )
                    logger.info(f"[{operation_id}] Email sent to {recipient}")

                except Exception as err:
                    logger.error(
                        f"[{operation_id}] Failed to send email to {recipient}: {err}"
                    )
                    metadata, status = (
                        {
                            "error": str(err),
                            "recipients_count": len(recipients),
                            "duration_seconds": round(time.time() - start_time, 3),
                        },
                        MailLog.MailStatus.FAILED,
                    )
                if log := mail_logs.filter(
                    mailing__user__email=recipient, operation_id=operation_id
                ).first():
                    log.update_metadata(metadata, status)
        else:
            status = MailLog.MailStatus.SENT
            try:
                send_mail(**data, fail_silently=False)
            except Exception as err:
                status = MailLog.MailStatus.FAILED
                logger.error(f"[{operation_id}] Failed to send BULK email: {err}")
            else:
                logger.info(
                    f"[{operation_id}] Email sent to {len(recipients)} recipients"
                )

            result = {
                "recipients_count": len(recipients),
                "duration_seconds": round(time.time() - start_time, 3),
                "subject": subject,
            }

            for log in mail_logs:
                log.update_metadata(result, status)

            if track_metrics:
                _update_email_metrics("bulk_success", len(recipients))

            return result

    except Exception as err:
        duration = time.time() - start_time
        error_result = {
            "status": "failed",
            "error": str(err),
            "recipients_count": len(recipients),
            "duration_seconds": round(duration, 2),
            "retry_count": self.request.retries,
        }

        logger.error(f"✗ Email failed: {error_result}")

        if track_metrics:
            _update_email_metrics("failure", len(recipients))

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            countdown = 60 * (2**self.request.retries)
            logger.info(
                f"Retrying in {countdown}s (attempt {self.request.retries + 1})"
            )
            raise self.retry(countdown=countdown)

        return error_result


def _update_email_metrics(metric_type: str, count: int):
    """Update email sending metrics in cache."""
    try:
        current = cache.get(f"email_metrics_{metric_type}", 0)
        cache.set(f"email_metrics_{metric_type}", current + count, 86400)  # 24h
    except:
        pass  # Don't fail task if metrics update fails
