from datetime import timedelta
from typing import List

import pytest
from django.utils import timezone

from mailing.schemas import EmailTemplateRegistry
from mailing.services import PostmanService
from premium.models import PremiumType
from users.models import User
from utils.factories import PlayerProfileFactory
from utils.factories.profiles_factories import (
    ClubProfileFactory,
    ProfileVideoFactory,
    ProfileVisitationFactory,
)
from utils.factories.transfers_factories import (
    TransferRequestFactory,
    TransferStatusFactory,
)
from utils.fixtures.profiles import CoachProfileFactory

pytestmark = pytest.mark.django_db
postman_service = PostmanService()


@pytest.fixture
def mock_timezone_now(monkeypatch):
    """Fikstura do mockowania timezone.now()"""

    def _mock_timezone_now(mock_time=None):
        if mock_time is None:
            mock_time = timezone.now()
        monkeypatch.setattr("mailing.services.timezone.now", lambda: mock_time)
        return mock_time

    return _mock_timezone_now


@pytest.fixture
def mock_current_time():
    """Fikstura zwracająca bieżący czas"""
    return timezone.now()


@pytest.fixture
def mock_time_plus_days():
    """Fikstura do tworzenia czasu z dodanymi dniami"""

    def _mock_time_plus_days(days):
        return timezone.now() + timedelta(days=days)

    return _mock_time_plus_days


class TestPostmanService:
    def _get_recipients_list(self, outbox, subject) -> List[str]:
        return [email.to[0] for email in outbox if email.subject == subject]

    def test_blank_profile(self, outbox) -> None:
        # Create users with date_joined > 3 days ago to pass new exclusion logic
        old_date = timezone.now() - timedelta(days=5)
        
        p1 = PlayerProfileFactory.create(
            user__declared_role="P", team_object=None, user__date_joined=old_date
        )
        p2 = PlayerProfileFactory.create(user__declared_role="P", user__date_joined=old_date)
        p3 = PlayerProfileFactory.create(
            user__declared_role="P", 
            user__display_status=User.DisplayStatus.NOT_SHOWN,
            user__date_joined=old_date
        )
        p4 = PlayerProfileFactory.create(
            user__declared_role="P", 
            user__display_status=User.DisplayStatus.VERIFIED,
            user__date_joined=old_date
        )  # filled profile
        ProfileVideoFactory.create(user=p4.user)
        t1 = CoachProfileFactory.create(
            user__declared_role="T", 
            user__display_status=User.DisplayStatus.NOT_SHOWN,
            user__date_joined=old_date
        )
        t2 = CoachProfileFactory.create(
            user__declared_role="T", 
            user__display_status=User.DisplayStatus.VERIFIED,
            user__date_joined=old_date
        )
        c1 = CoachProfileFactory.create(
            user__declared_role="C", 
            user__display_status=User.DisplayStatus.NOT_SHOWN,
            user__date_joined=old_date
        )
        c2 = CoachProfileFactory.create(
            user__declared_role="C", 
            user__display_status=User.DisplayStatus.VERIFIED,
            user__date_joined=old_date
        )
        outbox.clear()
        postman_service.blank_profile()
        recipients = [email.to[0] for email in outbox]

        assert len(outbox) == 5
        assert p1.user.email in recipients
        assert p2.user.email in recipients
        assert p3.user.email in recipients
        assert p4.user.email not in recipients
        assert t1.user.email in recipients
        assert t2.user.email not in recipients
        assert c1.user.email in recipients
        assert c2.user.email not in recipients

        postman_service.blank_profile()

        assert len(outbox) == 5  # No duplicate emails sent

    def test_inactive_for_30_days(self, outbox) -> None:
        now = timezone.now()
        p1 = PlayerProfileFactory.create(
            user__declared_role="P", user__last_activity=now - timedelta(days=29)
        )
        p2 = PlayerProfileFactory.create(
            user__declared_role="P", user__last_activity=now - timedelta(days=31)
        )

        outbox.clear()
        postman_service.inactive_for_30_days()
        recipients = [email.to[0] for email in outbox]

        assert len(outbox) == 1
        assert p1.user.email not in recipients
        assert p2.user.email in recipients

        postman_service.inactive_for_30_days()

        assert len(outbox) == 1

    def test_inactive_for_90_days(self, outbox) -> None:
        now = timezone.now()
        p1 = PlayerProfileFactory.create(
            user__declared_role="P",
            user__last_activity=now - timezone.timedelta(days=89),
        )
        p2 = PlayerProfileFactory.create(
            user__declared_role="P",
            user__last_activity=now - timezone.timedelta(days=91),
        )

        outbox.clear()
        postman_service.inactive_for_90_days()
        recipients = [email.to[0] for email in outbox]

        assert len(outbox) == 1
        assert p1.user.email not in recipients
        assert p2.user.email in recipients

        postman_service.inactive_for_90_days()

        assert len(outbox) == 1

    def test_go_premium(
        self, outbox, mock_timezone_now, mock_current_time, mock_time_plus_days
    ) -> None:
        # Create users with date_joined > 5 days ago to pass exclusion logic
        old_date = timezone.now() - timedelta(days=7)
        
        p1 = PlayerProfileFactory.create(
            user__declared_role="P",
            user__date_joined=old_date
        )
        p1.setup_premium_profile()
        p2 = PlayerProfileFactory.create(
            user__declared_role="P",
            user__date_joined=old_date
        )
        p2.setup_premium_profile(PremiumType.MONTH)
        p3 = PlayerProfileFactory.create(
            user__declared_role="P",
            user__date_joined=old_date
        )

        outbox.clear()
        mock_timezone_now(mock_current_time)
        postman_service.go_premium()
        recipients = self._get_recipients_list(
            outbox, EmailTemplateRegistry.PREMIUM_ENCOURAGEMENT.subject
        )

        assert len(recipients) == 1
        assert p1.user.email not in recipients
        assert p2.user.email not in recipients
        assert p3.user.email in recipients

        mock_timezone_now(mock_current_time)
        postman_service.go_premium()

        assert len(outbox) == 1

        mock_timezone_now(mock_time_plus_days(8))
        p1.refresh_from_db()
        assert not p1.is_premium
        postman_service.go_premium()

        recipients = self._get_recipients_list(
            outbox, EmailTemplateRegistry.PREMIUM_ENCOURAGEMENT.subject
        )

        assert len(recipients) == 2
        assert p1.user.email in recipients

        mock_timezone_now(mock_time_plus_days(100))
        p2.refresh_from_db()
        assert not p2.is_premium
        postman_service.go_premium()

        recipients = self._get_recipients_list(
            outbox, EmailTemplateRegistry.PREMIUM_ENCOURAGEMENT.subject
        )

        assert len(recipients) == 5
        assert recipients.count(p1.user.email) == 2
        assert recipients.count(p2.user.email) == 1
        assert recipients.count(p3.user.email) == 2

    def test_views_monthly(
        self, outbox, mock_timezone_now, mock_current_time, mock_time_plus_days
    ) -> None:
        now = mock_current_time
        p1 = PlayerProfileFactory.create(
            user__declared_role="P",
        )
        p2 = PlayerProfileFactory.create(
            user__declared_role="P",
        )
        ProfileVisitationFactory.create_batch(7, visited=p2.meta)
        p3 = PlayerProfileFactory.create(
            user__declared_role="P",
        )
        ProfileVisitationFactory.create_batch(4, visited=p3.meta)

        outbox.clear()
        mock_timezone_now(now)
        postman_service.views_monthly()
        recipients = self._get_recipients_list(
            outbox, EmailTemplateRegistry.PROFILE_VIEWS_MILESTONE.subject
        )

        assert len(recipients) == 1
        assert p1.user.email not in recipients
        assert p2.user.email in recipients
        assert p3.user.email not in recipients

        mock_timezone_now(mock_time_plus_days(2))
        postman_service.views_monthly()

        assert len(recipients) == 1

        ProfileVisitationFactory.create(timestamp=now, visited=p3.meta)

        mock_timezone_now(mock_time_plus_days(3))
        postman_service.views_monthly()

        recipients = self._get_recipients_list(
            outbox, EmailTemplateRegistry.PROFILE_VIEWS_MILESTONE.subject
        )
        assert len(recipients) == 2
        assert p3.user.email in recipients

    def test_player_without_transfer_status(
        self, outbox, mock_timezone_now, mock_time_plus_days
    ) -> None:
        outbox.clear()
        # Create users with date_joined > 7 days ago to pass exclusion logic
        old_date = timezone.now() - timedelta(days=12)
        
        p1 = PlayerProfileFactory.create(
            user__declared_role="P",
            user__date_joined=old_date
        )
        TransferStatusFactory.create(meta=p1.meta)
        p2 = PlayerProfileFactory.create(
            user__declared_role="P",
            user__date_joined=old_date
        )

        assert p2.meta.transfer_object is None

        postman_service.player_without_transfer_status()
        recipients = self._get_recipients_list(
            outbox, EmailTemplateRegistry.TRANSFER_STATUS_REMINDER.subject
        )

        assert len(recipients) == 1
        assert p2.user.email in recipients
        assert p1.user.email not in recipients

        p1.meta.transfer_object.delete()

        mock_timezone_now(mock_time_plus_days(34))
        postman_service.player_without_transfer_status()
        recipients = self._get_recipients_list(
            outbox, EmailTemplateRegistry.TRANSFER_STATUS_REMINDER.subject
        )

        assert len(recipients) == 2
        assert p2.user.email in recipients

        mock_timezone_now(mock_time_plus_days(31))
        postman_service.player_without_transfer_status()
        recipients = self._get_recipients_list(
            outbox, EmailTemplateRegistry.TRANSFER_STATUS_REMINDER.subject
        )

        assert len(recipients) == 3
        assert p2.user.email in recipients
        assert p1.user.email in recipients

    def test_profile_without_transfer_request(
        self, outbox, mock_timezone_now, mock_time_plus_days
    ) -> None:
        outbox.clear()
        # Create users with date_joined > 7 days ago to pass exclusion logic
        old_date = timezone.now() - timedelta(days=16)
        
        t1 = CoachProfileFactory.create(
            user__declared_role="T",
            user__date_joined=old_date
        )
        TransferRequestFactory.create(meta=t1.meta)
        c1 = ClubProfileFactory.create(user__declared_role="C", user__date_joined=old_date)

        postman_service.profile_without_transfer_request()
        recipients = self._get_recipients_list(
            outbox, EmailTemplateRegistry.TRANSFER_REQUEST_REMINDER.subject
        )

        assert len(recipients) == 1
        assert c1.user.email in recipients
        assert t1.user.email not in recipients

        t1.meta.transfer_request.delete()
        mock_timezone_now(mock_time_plus_days(34))
        postman_service.profile_without_transfer_request()
        recipients = self._get_recipients_list(
            outbox, EmailTemplateRegistry.TRANSFER_REQUEST_REMINDER.subject
        )
        assert len(recipients) == 2
        assert c1.user.email in recipients
        assert t1.user.email in recipients

        mock_timezone_now(mock_time_plus_days(30))
        postman_service.profile_without_transfer_request()
        recipients = self._get_recipients_list(
            outbox, EmailTemplateRegistry.TRANSFER_REQUEST_REMINDER.subject
        )
        assert len(recipients) == 3
        assert c1.user.email in recipients
        assert t1.user.email in recipients

    def test_invite_friends(
        self,
        outbox,
        mock_time_plus_days,
        mock_timezone_now,
    ) -> None:
        # Create users with date_joined > 10 days ago to pass exclusion logic
        old_date = timezone.now() - timedelta(days=16)
        
        player_profile = PlayerProfileFactory.create(
            user__declared_role="P",
            user__date_joined=old_date
        )
        coach_profile = CoachProfileFactory.create(
            user__declared_role="T",
            user__date_joined=old_date
        )
        
        outbox.clear()

        postman_service.invite_friends()
        recipients = self._get_recipients_list(
            outbox, EmailTemplateRegistry.INVITE_FRIENDS_REMINDER.subject
        )

        assert recipients.count(player_profile.user.email) == 1
        assert recipients.count(coach_profile.user.email) == 1

        mock_timezone_now(mock_time_plus_days(59))

        postman_service.invite_friends()
        recipients = self._get_recipients_list(
            outbox, EmailTemplateRegistry.INVITE_FRIENDS_REMINDER.subject
        )

        assert recipients.count(player_profile.user.email) == 1
        assert recipients.count(coach_profile.user.email) == 1

        mock_timezone_now(mock_time_plus_days(2))
        postman_service.invite_friends()
        recipients = self._get_recipients_list(
            outbox, EmailTemplateRegistry.INVITE_FRIENDS_REMINDER.subject
        )

        assert recipients.count(player_profile.user.email) == 2
        assert recipients.count(coach_profile.user.email) == 2
