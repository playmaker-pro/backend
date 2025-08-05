import pytest
from django.core import mail

from mailing.schemas import EmailTemplateRegistry, MailContent


@pytest.fixture(autouse=True)
def clear_mail_outbox():
    """Clear the mail outbox before each test."""
    mail.outbox.clear()


@pytest.fixture
def test_template() -> MailContent:
    """Fixture to provide an email template for the command."""
    return EmailTemplateRegistry.TEST
