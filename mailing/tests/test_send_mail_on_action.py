import pytest
from django.contrib.auth import get_user_model
from django.core import mail

from mailing.models import EmailTemplate as _EmailTemplate
from mailing.models import UserEmailOutbox as _UserEmailOutbox
from users.managers import UserTokenManager
from users.services import PasswordResetService

User = get_user_model()


@pytest.fixture
def new_user():
    yield User.objects.get_or_create(email="test@test.com")[0]


@pytest.mark.django_db
class TestSendMailForNewUser:
    def test_send_email_to_new_created_user(self, new_user) -> None:
        """Test send email to new created user"""
        last_outbox = _UserEmailOutbox.objects.last()

        assert len(mail.outbox) == 1
        assert mail.outbox[-1].to == [new_user.email]
        assert last_outbox.recipient == new_user.email, (
            last_outbox.email_type == _EmailTemplate.EmailType.NEW_USER
        )

    def test_send_email_to_reset_password(self, new_user) -> None:
        """Test send email to user to reset password"""
        mail.outbox.clear()
        assert len(mail.outbox) == 0
        reset_url = UserTokenManager.create_url(new_user)
        PasswordResetService.send_reset_email(new_user, reset_url)
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [new_user.email]

        last_outbox = _UserEmailOutbox.objects.last()
        assert last_outbox.recipient == new_user.email, (
            last_outbox.email_type == _EmailTemplate.EmailType.PASSWORD_CHANGE
        )

    def test_send_email_on_inquiry_limit_reached(self, new_user) -> None:
        """Test send email to user when inquiry limit reached"""
        mail.outbox.clear()
        new_user.userinquiry.counter = 1
        new_user.userinquiry.save()
        assert len(mail.outbox) == 0
        new_user.userinquiry.increment()
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [new_user.email]

        last_outbox = _UserEmailOutbox.objects.last()
        assert last_outbox.recipient == new_user.email, (
            last_outbox.email_type == _EmailTemplate.EmailType.INQUIRY_LIMIT
        )
