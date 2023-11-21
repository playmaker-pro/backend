import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail

from users.services import PasswordResetService

User = get_user_model()


@pytest.fixture
def new_user():
    yield User.objects.get_or_create(email="test@test.com")[0]


@pytest.mark.django_db
class TestSendMailForNewUser:
    def test_send_email_to_new_created_user(self, new_user) -> None:
        """Test send email to new created user"""
        assert len(mail.outbox) == 2
        assert [email.to[0] for email in mail.outbox] == [
            new_user.email,
            settings.SYSTEM_USER_EMAIL,
        ]

    def test_send_email_to_reset_password(self, new_user) -> None:
        """Test send email to user to reset password"""
        mail.outbox.clear()
        assert len(mail.outbox) == 0
        PasswordResetService.send_reset_email(new_user, "reset_url")
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [new_user.email]
