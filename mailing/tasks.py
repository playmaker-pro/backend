import logging
import time
from typing import Any, Dict, List

from celery import shared_task
from django.core.cache import cache
from django.core.mail import mail_admins, send_mail

logger: logging.Logger = logging.getLogger("mailing")


@shared_task
def notify_admins(**data):
    """Send notification to admins with error tracking."""
    try:
        mail_admins(**data)
        logger.info(f"Admin notification sent: {data.get('subject', 'No subject')}")
    except Exception as err:
        logger.error(f"Admin notification failed: {err}")
        # Track admin notification failures
        cache.set("admin_notification_last_error", str(err), 3600)
        raise


@shared_task(bind=True, max_retries=3)
def send(self, separate: bool = False, track_metrics: bool = True, **data):
    """
    Enhanced email sending with metrics and better error handling.
    """
    recipients = data.get("recipient_list", [])
    subject = data.get("subject", "No subject")
    start_time = time.time()

    # Input validation
    if not recipients:
        logger.warning("No recipients provided")
        return {"status": "skipped", "reason": "no_recipients"}

    if not subject or subject == "No subject":
        logger.warning("No subject provided")

    try:
        if separate:
            results = _send_separate_emails(recipients, data)
            _log_separate_results(results, subject)
            return results
        else:
            send_mail(**data)
            duration = time.time() - start_time

            result = {
                "status": "success",
                "recipients_count": len(recipients),
                "duration_seconds": round(duration, 2),
                "subject": subject,
            }

            logger.info(f"✓ Bulk email sent: {result}")

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


def _send_separate_emails(
    recipients: List[str], data: Dict[str, Any]
) -> Dict[str, Any]:
    """Send individual emails to each recipient."""
    successful = []
    failed = []

    for recipient in recipients:
        try:
            individual_data = data.copy()
            individual_data["recipient_list"] = [recipient]
            send_mail(**individual_data)
            successful.append(recipient)
        except Exception as err:
            failed.append({"recipient": recipient, "error": str(err)})

    return {
        "status": "completed",
        "successful": successful,
        "failed": failed,
        "success_count": len(successful),
        "failure_count": len(failed),
        "total_count": len(recipients),
    }


def _log_separate_results(results: Dict[str, Any], subject: str):
    """Log results of separate email sending."""
    success_count = results["success_count"]
    failure_count = results["failure_count"]
    total = results["total_count"]

    if failure_count == 0:
        logger.info(f"✓ All {total} individual emails sent successfully: {subject}")
    else:
        logger.warning(
            f"⚠ Mixed results: {success_count}/{total} successful: {subject}"
        )
        for failed in results["failed"]:
            logger.error(f"  ✗ {failed['recipient']}: {failed['error']}")


def _update_email_metrics(metric_type: str, count: int):
    """Update email sending metrics in cache."""
    try:
        current = cache.get(f"email_metrics_{metric_type}", 0)
        cache.set(f"email_metrics_{metric_type}", current + count, 86400)  # 24h
    except:
        pass  # Don't fail task if metrics update fails
