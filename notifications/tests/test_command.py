from io import StringIO

import pytest
from django.core.management import call_command

from notifications.models import Notification
from utils.factories.profiles_factories import (
    ClubProfileFactory,
    CoachProfileFactory,
    GuestProfileFactory,
    ManagerProfileFactory,
    PlayerProfileFactory,
    ScoutProfileFactory,
)

pytestmark = pytest.mark.django_db


class TestSendCustomNotificationCommand:
    """Test suite for send_custom_notification management command."""

    @pytest.fixture(autouse=True)
    def setup_profiles(self):
        """Create test profiles for different user types."""
        PlayerProfileFactory()
        CoachProfileFactory()
        ScoutProfileFactory()
        ClubProfileFactory()
        GuestProfileFactory()
        ManagerProfileFactory()

    @pytest.mark.parametrize(
        "args, expected_count",
        (
            (
                [
                    "--title",
                    "Sometitle",
                    "--description",
                    "Somedescription",
                    "--icon",
                    "SomeIcon",
                    "--href",
                    "/SomeHref",
                    "--all",
                ],
                6,
            ),
            (
                [
                    "--title",
                    "RandomTitle1",
                    "--description",
                    "Desc1",
                    "--icon",
                    "IconA",
                    "--href",
                    "/HrefA",
                    "--players",
                ],
                1,
            ),
            (
                [
                    "--title",
                    "AnotherTitle",
                    "--description",
                    "AnotherDesc",
                    "--icon",
                    "IconB",
                    "--href",
                    "/HrefB",
                    "--coaches",
                ],
                1,
            ),
            (
                [
                    "--title",
                    "Test123",
                    "--description",
                    "TestDesc",
                    "--href",
                    "/TestHref",
                    "--scouts",
                ],
                1,
            ),
            (
                [
                    "--title",
                    "Lorem Ipsum",
                    "--description",
                    "Dolor sit amet",
                    "--icon",
                    "IconLorem",
                    "--clubs",
                ],
                1,
            ),
            (
                [
                    "--title",
                    "Alpha",
                    "--description",
                    "Beta",
                    "--icon",
                    "Gamma",
                    "--href",
                    "/delta",
                    "--guests",
                ],
                1,
            ),
            (
                [
                    "--title",
                    "nhnhnhn",
                    "--description",
                    "erterte",
                    "--guests",
                    "--clubs",
                    "--coaches",
                ],
                3,
            ),
            (
                [
                    "--title",
                    "Zeta",
                    "--description",
                    "Eta",
                    "--managers",
                    "--coaches",
                    "--scouts",
                    "--players",
                ],
                4,
            ),
            (
                [
                    "--title",
                    "UniqueTitle",
                    "--description",
                    "UniqueDesc",
                    "--icon",
                    "UniqueIcon",
                    "--href",
                    "/unique",
                    "--all",
                    "--players",
                ],
                6,
            ),
        ),
    )
    def test_run_command(self, args, expected_count):
        call_command(
            "send_custom_notification",
            *args,
            stdout=(stdout := StringIO()),
        )
        out = stdout.getvalue()
        query_data = {"title": args[1], "description": args[3]}
        if args[4] == "--icon":
            query_data["icon"] = args[5]
        if args[6] == "--href":
            query_data["href"] = args[7]

        assert out.startswith("Notifications sent successfully to")
        assert out.endswith(
            f"\nSUCCESS: {expected_count}, FAILED: 0, TOTAL: {expected_count}\n"
        )
        assert Notification.objects.filter(**query_data).count() == expected_count
