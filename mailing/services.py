from mailing.schemas import Envelope, MailContent
from users.models import User


class MailingService:
    """Handles sending templated emails and optionally logging them in the outbox."""

    def __init__(self, schema: MailContent) -> None:
        """
        Initialize the mailing service.

        Args:
            schema (MailContent): The email template schema to use.
        """
        if schema is None:
            raise ValueError("Schema cannot be None")
        self._schema = schema

    def send_mail(self, recipient: User) -> None:
        """
        Send the email using the provided schema and recipient.
        """
        envelope = Envelope(mail=self._schema, recipients=[recipient.email])
        envelope.send()

    def send_mail_to_admins(self) -> None:
        """
        Send the email to admins using the provided schema.
        """
        envelope = Envelope(mail=self._schema)
        envelope.send_to_admins()
