import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandParser

from mailing.management.commands.send_email import Command as SendEmailCommand

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestCommandSendEmail:
    @pytest.mark.parametrize(
        "recipients,recipients_count",
        (
            ("--players", 1),
            ("--coaches --players", 2),
            ("--all", 4),
            (f"--guests --others '{settings.SYSTEM_USER_EMAIL}'", 2),
        ),
    )
    def test_command_send_email(
        self,
        recipients,
        recipients_count,
        player_profile,
        coach_profile,
        guest_profile,
        manager_profile,
        test_template,
        outbox,
    ):
        """Test the command to send email notifications."""
        outbox.clear()
        command = SendEmailCommand()
        parser = CommandParser()
        command.add_arguments(parser)

        args = [
            "--title",
            test_template.subject,
            "--template_path",
            test_template.template_path,
        ] + recipients.split()

        options = parser.parse_args(args)
        options = vars(options)

        command.handle(**options)

        assert len(outbox) == recipients_count

    @pytest.mark.parametrize("recipients", ["players", "coaches", "all"])
    def test_command_simple_parametrized(
        self, recipients, test_template, player_profile, coach_profile, outbox
    ):
        """Simple parametrized test using call_command."""
        outbox.clear()
        call_command(
            "send_email",
            f"--{recipients}",
            "--title",
            test_template.subject,
            "--template_path",
            test_template.template_path,
        )

        assert len(outbox) == 2 if recipients == "all" else 1
