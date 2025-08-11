from django.db import models
from django.utils.translation import gettext_lazy as _

from mailing.schemas import EmailTemplateRegistry


class InquiryLogType(models.TextChoices):
    """Inquiry log message types."""

    ACCEPTED = "ACCEPTED_INQUIRY", _("Accepted inquiry")
    REJECTED = "REJECTED_INQUIRY", _("Rejected inquiry")
    NEW = "NEW_INQUIRY", _("New inquiry")
    OUTDATED = "OUTDATED_INQUIRY", _("Outdated inquiry")
    UNDEFINED = "UNDEFINED_INQUIRY", _("Undefined inquiry")
    OUTDATED_REMINDER = "OUTDATED_REMINDER", _("Reminder about outdated inquiry")


# Mapping of log types that should trigger email sending
EMAIL_ENABLED_LOG_TYPES = {
    InquiryLogType.ACCEPTED,
    InquiryLogType.REJECTED,
    InquiryLogType.NEW,
    InquiryLogType.OUTDATED,
    InquiryLogType.OUTDATED_REMINDER,
}


INQUIRY_EMAIL_TEMPLATE = {
    InquiryLogType.ACCEPTED: EmailTemplateRegistry.ACCEPTED_INQUIRY,
    InquiryLogType.REJECTED: EmailTemplateRegistry.REJECTED_INQUIRY,
    InquiryLogType.NEW: EmailTemplateRegistry.NEW_INQUIRY,
    InquiryLogType.OUTDATED: EmailTemplateRegistry.OUTDATED_INQUIRY,
    InquiryLogType.OUTDATED_REMINDER: EmailTemplateRegistry.OUTDATED_REMINDER,
}
