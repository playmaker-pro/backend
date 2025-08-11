import pytest
from django.core.management import call_command


@pytest.mark.django_db
class TestSendEmailCommand:
    """Test cases for the send_email management command."""

    def test_command_with_players(
        self, test_template, outbox, player_profile, coach_profile, scout_profile
    ):
        """Test sending emails to players only."""
        call_command(
            "send_email",
            "--players",
            "--title",
            test_template.subject,
            "--template_path",
            test_template.template_path,
        )

        assert len(outbox) == 1
        assert outbox[0].to == [player_profile.user.email]

    def test_command_with_multiple_recipients(
        self, test_template, outbox, player_profile, coach_profile, scout_profile
    ):
        """Test sending emails to multiple recipient types."""
        call_command(
            "send_email",
            "--players",
            "--coaches",
            "--title",
            test_template.subject,
            "--template_path",
            test_template.template_path,
        )

        received_by = [mail.to[0] for mail in outbox]
        assert len(outbox) == 2
        assert player_profile.user.email in received_by
        assert coach_profile.user.email in received_by
        assert scout_profile.user.email not in received_by

    def test_command_with_others(self, test_template, outbox):
        """Test sending emails to additional recipients."""
        call_command(
            "send_email",
            "--others",
            "extra1@test.com;extra2@test.com",
            "--title",
            test_template.subject,
            "--template_path",
            test_template.template_path,
        )

        received_by = [mail.to[0] for mail in outbox]
        assert len(outbox) == 2
        assert "extra1@test.com" in received_by
        assert "extra2@test.com" in received_by
