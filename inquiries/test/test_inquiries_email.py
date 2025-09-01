from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model

from inquiries.constants import InquiryLogType
from inquiries.errors import ForbiddenLogAction
from inquiries.models import InquiryRequest, UserInquiry
from mailing.models import MailLog
from mailing.schemas import EmailTemplateFileNames

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestSendEmails:
    @pytest.fixture
    def coach_profile(self, coach_profile):
        """Create a coach profile for testing"""
        coach_profile.user.userpreferences.gender = "K"
        coach_profile.user.userpreferences.save()
        coach_profile.user.first_name = "Karolina"
        coach_profile.user.last_name = "Nowak"
        coach_profile.user.save()
        return coach_profile

    @pytest.fixture
    def player_profile(self, player_profile):
        """Create a player profile for testing"""
        player_profile.user.userpreferences.gender = "M"
        player_profile.user.userpreferences.save()
        player_profile.user.first_name = "Jan"
        player_profile.user.last_name = "Kowalski"
        player_profile.user.save()
        return player_profile

    def test_send_email_on_send_request(self, player_profile, coach_profile) -> None:
        """Send email to recipient on new request"""
        InquiryRequest.objects.create(
            sender=player_profile.user, recipient=coach_profile.user
        )

        assert MailLog.objects.filter(mailing__user=coach_profile.user).exists()

    def test_send_email_on_accepted_request(
        self, player_profile, coach_profile
    ) -> None:
        """Send email to sender on accept request"""
        inquiry_request = InquiryRequest.objects.create(
            sender=coach_profile.user, recipient=player_profile.user
        )
        inquiry_request.accept()
        inquiry_request.save()

        assert MailLog.objects.filter(
            mailing__user=coach_profile.user,
            mail_template=EmailTemplateFileNames.ACCEPTED_INQUIRY.value,
        ).exists()

    def test_send_email_on_reject_request(self, player_profile, coach_profile) -> None:
        """Send email to sender on reject request"""
        inquiry_request = InquiryRequest.objects.create(
            sender=player_profile.user, recipient=coach_profile.user
        )
        inquiry_request.reject()
        inquiry_request.save()

        assert MailLog.objects.filter(
            mailing__user=player_profile.user,
            mail_template=EmailTemplateFileNames.REJECTED_INQUIRY.value,
        ).exists()

    def test_send_email_on_outdated_request_to_sender(
        self, player_profile, coach_profile
    ) -> None:
        """Send email to sender on outdated request"""
        inquiry_request = InquiryRequest.objects.create(
            sender=player_profile.user, recipient=coach_profile.user
        )

        _3days_back = inquiry_request.created_at - timedelta(days=4, hours=1)
        _6days_back = inquiry_request.created_at - timedelta(days=6, hours=1)
        _any_other_time = inquiry_request.created_at - timedelta(days=100)

        assert not inquiry_request.logs.filter(
            log_type=InquiryLogType.OUTDATED_REMINDER
        ).exists()

        inquiry_request.created_at = _3days_back
        inquiry_request.save()
        inquiry_request.refresh_from_db()
        assert (
            inquiry_request.__class__.objects.to_remind_recipient_about_outdated().count()  # noqa
            == 1
        )

        inquiry_request.notify_recipient_about_outdated()
        inquiry_request.refresh_from_db()

        assert (
            inquiry_request.__class__.objects.to_remind_recipient_about_outdated().count()  # noqa
            == 0
        )
        assert (
            inquiry_request.logs.filter(
                log_type=InquiryLogType.OUTDATED_REMINDER
            ).count()
            == 1
        )

        latest_mail = (
            MailLog.objects.filter(mailing__user=inquiry_request.recipient)
            .order_by("-sent_at")
            .first()
        )
        assert latest_mail is not None
        assert (
            latest_mail.subject
            == "Masz zapytanie o piłkarski kontakt czekające na decyzję."
        )

        # second time should not be sent without changing date
        with pytest.raises(ForbiddenLogAction):
            inquiry_request.notify_recipient_about_outdated()

        inquiry_request.created_at = _6days_back
        inquiry_request.save()

        assert (
            inquiry_request.__class__.objects.to_remind_recipient_about_outdated().count()  # noqa
            == 1
        )

        inquiry_request.notify_recipient_about_outdated()
        inquiry_request.refresh_from_db()

        latest_mail = (
            MailLog.objects.filter(mailing__user=inquiry_request.recipient)
            .order_by("-sent_at")
            .first()
        )
        assert latest_mail is not None
        assert (
            latest_mail.subject
            == "Masz zapytanie o piłkarski kontakt czekające na decyzję."
        )
        assert (
            inquiry_request.logs.filter(
                log_type=InquiryLogType.OUTDATED_REMINDER
            ).count()
            == 2
        )

        inquiry_request.created_at = _any_other_time
        inquiry_request.save()

        # recipient should not be notified anymore
        with pytest.raises(ForbiddenLogAction):
            inquiry_request.notify_recipient_about_outdated()

    def test_send_email_on_reward_sender(self, player_profile, coach_profile) -> None:
        """Send email to sender on reward sender"""
        inquiry_request = InquiryRequest.objects.create(
            sender=player_profile.user, recipient=coach_profile.user
        )

        _7days_back = inquiry_request.created_at - timedelta(days=7, hours=1)
        inquiry_request.created_at = _7days_back
        inquiry_request.save()
        inquiry_request.reward_sender()

        latest_mail = MailLog.objects.filter(
            mailing__user=inquiry_request.sender,
            mail_template=EmailTemplateFileNames.OUTDATED_INQUIRY.value,
        ).first()
        assert latest_mail is not None
        assert (
            latest_mail.subject == "Zwiększamy Twoją pulę zapytań o piłkarski kontakt!"
        )

        # Assert we can't reward sender twice
        with pytest.raises(ForbiddenLogAction):
            inquiry_request.reward_sender()

    def test_send_email_on_limit_reached(self, player_profile, coach_profile) -> None:
        """Send email to user if he reached inquiry requests limit"""
        player_profile.user.userinquiry.counter = 2
        player_profile.user.userinquiry.save()

        limit_reached = UserInquiry.objects.limit_reached()
        assert limit_reached.count() == 1, (
            limit_reached.first().user == player_profile.user
        )

        latest_mail = MailLog.objects.filter(
            mailing__user=player_profile.user,
            mail_template=EmailTemplateFileNames.INQUIRY_LIMIT.value,
        ).first()
        assert latest_mail is not None
        assert (
            latest_mail.subject
            == "Rozbuduj swoje transferowe możliwości – Rozszerz limit zapytań!"
        )
