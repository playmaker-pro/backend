from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from mailing.schemas import EmailSchema as _EmailSchema
from mailing.services import MailingService as _MailingService
from mailing.services import MessageContentParser as _MessageContentParser


class UserEmailOutbox(models.Model):
    """Model for storing information about sent emails."""

    recipient = models.EmailField()
    sent_date = models.DateTimeField(auto_now_add=True)
    email_type = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"Recipient: {self.recipient} -- Type: {self.email_type}"


class EmailTemplate(models.Model):
    """Email template model."""

    class EmailManager(models.Manager):
        def new_user_template(self) -> "EmailTemplate":
            """Return default new user email template."""
            return self.get(email_type=self.model.EmailType.NEW_USER, is_default=True)

        def password_reset_template(self) -> "EmailTemplate":
            """Return default password reset email template."""
            return self.get(
                email_type=self.model.EmailType.PASSWORD_CHANGE, is_default=True
            )

        def inquiry_limit_reached_template(self) -> "EmailTemplate":
            """Return default email template about reaching inquiry limit."""
            return self.get(
                email_type=self.model.EmailType.INQUIRY_LIMIT, is_default=True
            )

        def can_sent_inquiry_limit_reached_email(
            self, user: settings.AUTH_USER_MODEL
        ) -> bool:
            """
            Return True if user can receive inquiry limit reached email.

            Send email once per round. So:
            - if last email was sent in april current year, we can sent next email after june current year.
            - if last email was sent in july current year, we can sent next email after december current year.
            - if last email was sent in december last year, we can sent next email after june current year.
            """
            curr_date = timezone.now()
            if not (
                last_sent_mail := (
                    UserEmailOutbox.objects.filter(
                        recipient=user.email,
                        email_type=self.model.EmailType.INQUIRY_LIMIT,
                    ).last()
                )
            ):
                return True
            last_sent_mail = last_sent_mail.sent_date
            if last_sent_mail.month < 6:
                # last_sent | current_date | result
                # 2023-04-01 | 2023-06-01 | True
                # 2023-04-01 | 2023-05-01 | False
                # 2023-04-01 | 2025-04-01 | True
                return (
                    True
                    if (curr_date.month >= 6 and curr_date.year >= last_sent_mail.year)
                    or curr_date.year > last_sent_mail.year + 1
                    else False
                )
            elif last_sent_mail.month == 12:
                # last_sent | current_date | result
                # 2022-12-03 | 2023-06-01 | True
                # 2022-12-03 | 2024-04-01 | True
                # 2022-12-03 | 2023-04-01 | False
                return (
                    True
                    if (curr_date.month >= 6 and curr_date.year > last_sent_mail.year)
                    or curr_date.year > last_sent_mail.year + 1
                    else False
                )
            elif last_sent_mail.month >= 6:
                # last_sent | current_date | result
                # 2023-06-01 | 2023-12-01 | True
                # 2023-07-01 | 2023-11-01 | False
                # 2023-07-01 | 2025-11-01 | True
                return (
                    True
                    if curr_date.month == 12 or curr_date.year > last_sent_mail.year
                    else False
                )

    _content_parser: _MessageContentParser = _MessageContentParser
    objects = EmailManager()

    EMAIL_PATTERN = _(
        "Type '#male_form|female_form#' - to mark something that "
        "should be determined by recipient gender (e.g. #Otrzymałeś|Otrzymałaś#). "
        "#url# as placeholder for some url."
    )

    class Meta:
        verbose_name = "Email template"
        verbose_name_plural = "Email templates"
        unique_together = ("email_type", "is_default")

    class EmailType(models.TextChoices):
        """Email type choices."""

        NEW_USER = "NEW_USER", "NEW_USER"
        PASSWORD_CHANGE = "PASSWORD_CHANGE", "PASSWORD_CHANGE"
        INQUIRY_LIMIT = "INQUIRY_LIMIT", "INQUIRY_LIMIT"
        ...

    subject = models.CharField(max_length=255)
    body = models.TextField(help_text=EMAIL_PATTERN)
    email_type = models.CharField(max_length=255, choices=EmailType.choices)
    is_default = models.BooleanField(
        _("Is default email template for selected type?"), default=True
    )

    def save(self, *args, **kwargs):
        """Save method, ensure that only one template for type is default."""
        if self.is_default:
            EmailTemplate.objects.filter(
                email_type=self.email_type, is_default=True
            ).update(is_default=False)
        super().save(*args, **kwargs)

    def create_email_schema(
        self, user: settings.AUTH_USER_MODEL, **extra_kwargs
    ) -> _EmailSchema:
        """
        Create email schema based on email subject, body and given user.
        """
        parser = self._content_parser(user, **extra_kwargs)
        subject = parser.parse_email_title(self.subject)
        body = parser.parse_email_body(self.body)
        return _EmailSchema(
            subject=subject, body=body, recipients=[user.email], type=self.email_type
        )

    @classmethod
    def send_email(cls, schema: _EmailSchema) -> None:
        """Fulfill email subject and body, then send email to user."""
        service = _MailingService(schema)
        service.send_mail()
        cls.add_outbox_record(schema)

    @staticmethod
    def add_outbox_record(schema: _EmailSchema) -> None:
        """Add record to outbox for each recipient."""
        for recipient in schema.recipients:
            UserEmailOutbox.objects.create(recipient=recipient, email_type=schema.type)

    @property
    def has_substitute(self) -> bool:
        """Does current template has substitute?"""
        return (
            self.objects.filter(email_type=self.email_type).exclude(pk=self.pk).exists()
        )

    def delete(self, *args, **kwargs):
        """Override delete method, ensure that there is always one template for type."""
        if not self.has_substitute:
            raise ValidationError(
                "Cannot delete this template if no other template for this type exists."
            )
        super().delete(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.email_type} -- {self.subject}"
