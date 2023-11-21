from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from mailing.schemas import EmailSchema as _EmailSchema
from mailing.services import MailingService as _MailingService
from mailing.services import MessageContentParser as _MessageContentParser


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
        return _EmailSchema(subject=subject, body=body, recipients=[user.email])

    @staticmethod
    def send_email(schema: _EmailSchema) -> None:
        """Fulfill email subject and body, then send email to user."""
        _MailingService.send_mail(schema)

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
