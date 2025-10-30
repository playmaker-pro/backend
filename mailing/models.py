import uuid
from typing import Any, Dict

from django.db import models

from mailing.schemas import EmailTemplateFileNames
from users.models import User


class MailingPreferences(models.Model):
    """
    Represents user preferences for receiving emails.
    """

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    system = models.BooleanField(default=True)
    marketing = models.BooleanField(default=True)


class Mailing(models.Model):
    """
    Represents a mailing that can be sent to users.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    preferences = models.OneToOneField(
        MailingPreferences,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )

    def save(self, *args, **kwargs):
        if not self.preferences_id:
            self.preferences = MailingPreferences.objects.create()
        super().save(*args, **kwargs)

    def __str__(self):
        return "Mailing of " + str(self.user)


class MailLog(models.Model):
    """
    Represents a log entry for an email sent to a user.
    """

    class MailStatus(models.TextChoices):
        SENT = "SENT", "SENT"
        FAILED = "FAILED", "FAILED"
        PENDING = "PENDING", "PENDING"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    operation_id = models.UUIDField(unique=False, null=True, blank=True)

    mailing = models.ForeignKey(
        Mailing, on_delete=models.CASCADE, related_name="mailbox"
    )
    subject = models.CharField(max_length=255, null=True, blank=True)
    mail_template = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        choices=[(name, name) for name in EmailTemplateFileNames],
    )
    status = models.CharField(
        max_length=50,
        choices=MailStatus.choices,
        default=MailStatus.PENDING,
    )
    metadata = models.JSONField(default=dict, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        title = f"{self.subject if self.subject else ''}"
        if self.mail_template:
            title += f"[{self.mail_template}]"
        return f"[{self.mailing.user.email}] {title} -- {self.created_at}"

    def update_metadata(self, data: Dict[str, Any], status: str) -> None:
        """
        Update the metadata for the mail log entry.
        """
        self.metadata = data
        self.status = status
        self.save()
