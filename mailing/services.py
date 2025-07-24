from django.conf import settings

from mailing.schemas import EmailTemplateRegistry, MailContent
from mailing.tasks import send
from mailing.utils import build_email_context


class MailingService:
    """Handles sending templated emails and optionally logging them in the outbox."""

    def __init__(self, schema: MailContent) -> None:
        """
        Initialize the mailing service.

        Args:
            schema (MailContent): The email template schema to use.
        """
        self._schema = schema

    def send_mail(self, recipient: settings.AUTH_USER_MODEL) -> None:
        """
        Send the email using the provided schema and recipient.
        """
        recipient_list = [recipient.email]

        send.delay(
            recipient_list=recipient_list,
            **self._schema.data,
        )


class TransactionalEmailService:
    """
    A service class for composing and sending templated emails,
    using contextual information from a user and optionally a log entry.
    """

    def __init__(self, user, log=None, context=None, **kwargs) -> None:
        """
        Initialize the TransactionalEmailService.

        Args:
            user: The main user receiving or sending the email.
            log (optional): A log entry with additional context.
            context (optional): Extra custom context for templates.
            **kwargs: Additional context variables.
        """
        self.user = user
        self.log = log
        self.context = build_email_context(user, log, context, **kwargs)

    def send(self, template_key: str, email_type: str, recipients: list = None) -> None:
        """Send a templated email to recipients."""
        mail_content = EmailTemplateRegistry.get(template_key)
        MailingService(
            context=self.context,
            recipients=recipients or [self.user.email],
            email_type=email_type,
            mail_content=mail_content,
        ).send_mail()
