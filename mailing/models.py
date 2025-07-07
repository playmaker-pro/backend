from django.db import models


class UserEmailOutbox(models.Model):
    """Model for storing information about sent emails."""

    recipient = models.EmailField()
    sent_date = models.DateTimeField(auto_now_add=True)
    email_type = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"Recipient: {self.recipient} -- Type: {self.email_type}"
