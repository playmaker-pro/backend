from django.utils.html import strip_tags

from mailing.models import UserEmailOutbox
from mailing.schemas import EmailTemplateRegistry, MailContent
from mailing.tasks import send
from mailing.utils import build_email_context


class MailingService:
    """Handles sending templated emails and optionally logging them in the outbox."""

    def __init__(
        self,
        context: dict,
        recipients: list,
        mail_content: MailContent,
        sender: str = None,
        email_type: str = None,
    ) -> None:
        """
        Initialize the mailing service.

        Args:
            context (dict): Context passed to the template renderer.
            recipients (list): List of recipient email addresses.
            mail_content (MailContent): Email template content.
            sender (str, optional): Email sender address.
            email_type (str, optional): Optional identifier for tracking/logging.
        """
        self.context = context
        self.recipients = recipients
        self.sender = sender
        self.mail_content = mail_content
        self.email_type = email_type

    def send_mail(self) -> None:
        """
        Send the email using the provided content, context, and recipients.
        Adds an outbox record if email_type is provided.
        """
        if not self.mail_content:
            raise ValueError("mail_content must be provided")

        subject = self.mail_content.parse_subject(context=self.context)
        body_html = self.mail_content.parse_template(context=self.context)
        body_text = strip_tags(body_html)  # fallback plain text

        if self.email_type:
            self.add_outbox_record()

        send.delay(
            subject=self._subject,
            message=self._body,
            from_email=self._sender,
            recipient_list=self._recipients,
            html_message=self._schema.html_body or None,
            log=self._schema.log,
        )

    def add_outbox_record(self) -> None:
        """
        Add an outbox tracking record for each recipient.
        Only called if email_type is specified.
        """
        for recipient in self.recipients:
            UserEmailOutbox.objects.create(
                recipient=recipient, email_type=self.email_type
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
            recipients=recipients or [self.user.contact_email],
            email_type=email_type,
            mail_content=mail_content,
        ).send_mail()
