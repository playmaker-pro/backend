from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from app.management.commands.daily_supervisor import Command as DailySupervisorCommand
from utils.factories.profiles_factories import PlayerProfileFactory

pytestmark = pytest.mark.django_db
User = get_user_model()


@pytest.fixture
def mock_timezone_now():
    time_now = timezone.now()
    with patch("app.management.commands.daily_supervisor.timezone.now") as mock_now:
        mock_now.return_value = time_now
        yield mock_now


class TestDailySupervisorCommand:
    @pytest.fixture
    def command(self):
        return DailySupervisorCommand()

    @pytest.mark.parametrize(
        "factory_kwargs",
        [
            {"team_object": None},
            {"user__display_status": User.DisplayStatus.NOT_SHOWN},
            {
                "user__display_status": User.DisplayStatus.NOT_SHOWN,
                "team_object": None,
            },
        ],
    )
    def test_blank_profile_for_player(self, command, factory_kwargs, mock_timezone_now):
        player_profile = PlayerProfileFactory.create(**factory_kwargs)
        player_profile.user.user_video.set([])
        # breakpoint()
        player_profile.user.mailing.mailbox.all().delete()  # TODO: Remove
        assert player_profile.user.mailing.mailbox.count() == 0

        command.blank_profile()
        player_profile.user.refresh_from_db()

        assert player_profile.user.mailing.mailbox.count() == 1

        mock_timezone_now.return_value += timezone.timedelta(days=15)
        command.blank_profile()

        assert (
            player_profile.user.mailing.mailbox.count() == 1
        )  # No new email within 30 days

        mock_timezone_now.return_value += timezone.timedelta(days=16)
        command.blank_profile()

        assert (
            player_profile.user.mailing.mailbox.count() == 2
        )  # New email after 30 days

    def test_blank_profile_for_club(self, command, mock_timezone_now, club_profile):
        club_profile.user.display_status = User.DisplayStatus.NOT_SHOWN
        club_profile.user.save()
        club_profile.user.mailing.mailbox.all().delete()  # TODO: Remove
        assert club_profile.user.mailing.mailbox.count() == 0

        command.blank_profile()
        club_profile.user.refresh_from_db()

        assert club_profile.user.mailing.mailbox.count() == 1

        mock_timezone_now.return_value += timezone.timedelta(days=15)
        command.blank_profile()

        assert (
            club_profile.user.mailing.mailbox.count() == 1
        )  # No new email within 30 days

        mock_timezone_now.return_value += timezone.timedelta(days=16)
        command.blank_profile()

        assert club_profile.user.mailing.mailbox.count() == 2  # New email after 30 days

    def test_blank_profile_for_coach(self, command, mock_timezone_now, coach_profile):
        coach_profile.user.display_status = User.DisplayStatus.NOT_SHOWN
        coach_profile.user.save()
        coach_profile.user.mailing.mailbox.all().delete()  # TODO: Remove

        assert coach_profile.user.mailing.mailbox.count() == 0

        command.blank_profile()
        coach_profile.user.refresh_from_db()

        assert coach_profile.user.mailing.mailbox.count() == 1

        mock_timezone_now.return_value += timezone.timedelta(days=15)
        command.blank_profile()

        assert (
            coach_profile.user.mailing.mailbox.count() == 1
        )  # No new email within 30 days

        mock_timezone_now.return_value += timezone.timedelta(days=16)
        command.blank_profile()

        assert (
            coach_profile.user.mailing.mailbox.count() == 2
        )  # New email after 30 days

    def test_inactive_for_30_days(self, command, mock_timezone_now, player_profile):
        player_profile.user.last_activity = timezone.now()
        player_profile.user.save()
        player_profile.user.mailing.mailbox.all().delete()  # TODO: Remove
        mock_timezone_now.return_value += timezone.timedelta(days=20)

        assert player_profile.user.mailing.mailbox.count() == 0

        command.inactive_for_30_days()
        player_profile.user.refresh_from_db()

        assert player_profile.user.mailing.mailbox.count() == 0

        mock_timezone_now.return_value += timezone.timedelta(days=11)
        command.inactive_for_30_days()
        player_profile.user.refresh_from_db()

        assert player_profile.user.mailing.mailbox.count() == 1

        mock_timezone_now.return_value += timezone.timedelta(days=1)
        command.inactive_for_30_days()
        player_profile.user.refresh_from_db()

        assert player_profile.user.mailing.mailbox.count() == 1

        mock_timezone_now.return_value += timezone.timedelta(days=300)
        command.inactive_for_30_days()
        player_profile.user.refresh_from_db()

        assert player_profile.user.mailing.mailbox.count() == 1

        player_profile.user.last_activity = mock_timezone_now.return_value
        player_profile.user.save()
        command.inactive_for_30_days()
        player_profile.user.refresh_from_db()

        assert player_profile.user.mailing.mailbox.count() == 1

        mock_timezone_now.return_value += timezone.timedelta(days=31)
        command.inactive_for_30_days()
        player_profile.user.refresh_from_db()

        assert player_profile.user.mailing.mailbox.count() == 2

    def test_inactive_for_90_days(self, command, mock_timezone_now, player_profile):
        player_profile.user.last_activity = timezone.now()
        player_profile.user.save()
        player_profile.user.mailing.mailbox.all().delete()
        mock_timezone_now.return_value += timezone.timedelta(days=80)

        assert player_profile.user.mailing.mailbox.count() == 0

        command.inactive_for_90_days()
        player_profile.user.refresh_from_db()

        assert player_profile.user.mailing.mailbox.count() == 0

        mock_timezone_now.return_value += timezone.timedelta(days=11)
        command.inactive_for_90_days()
        player_profile.user.refresh_from_db()

        assert player_profile.user.mailing.mailbox.count() == 1

        mock_timezone_now.return_value += timezone.timedelta(days=1)
        command.inactive_for_90_days()
        player_profile.user.refresh_from_db()

        assert player_profile.user.mailing.mailbox.count() == 1

        mock_timezone_now.return_value += timezone.timedelta(days=300)
        command.inactive_for_90_days()
        player_profile.user.refresh_from_db()

        assert player_profile.user.mailing.mailbox.count() == 1

        player_profile.user.last_activity = mock_timezone_now.return_value
        player_profile.user.save()
        command.inactive_for_90_days()
        player_profile.user.refresh_from_db()

        assert player_profile.user.mailing.mailbox.count() == 1

        mock_timezone_now.return_value += timezone.timedelta(days=91)
        command.inactive_for_90_days()
        player_profile.user.refresh_from_db()

        assert player_profile.user.mailing.mailbox.count() == 2
