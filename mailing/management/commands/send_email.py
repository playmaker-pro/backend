from dataclasses import dataclass
from typing import Any, Dict, List, Set

from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from mailing.tasks import send_many
from mailing.utils import extract_text_from_html
from profiles.models import ProfileMeta


@dataclass
class Args:
    """
    Dataclass to hold command arguments.
    """

    players: bool = False
    coaches: bool = False
    scouts: bool = False
    clubs: bool = False
    guests: bool = False
    managers: bool = False
    all: bool = False
    others: str = ""  # Comma-separated list of additional email addresses


class Command(BaseCommand):
    """
    Command to send custom emails to users.
    """

    help = "Send custom email to users"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.args: Args = None

    def handle(self, *args, **options):
        self._set_args(options)
        recipients: Set[str] = self._get_recipients()

        if not recipients:
            self.stdout.write(self.style.WARNING("No recipients found."))
            return

        html_content = render_to_string("emails/welcome.html")
        txt_content = extract_text_from_html(html_content)

        send_many.delay(
            recipients=list(recipients),
            subject=self.args.title,
            message=txt_content,
            html_message=html_content,
        )

    def add_arguments(self, parser):
        parser.add_argument(
            "--title",
            type=str,
            required=True,
            help="Title of the email",
        )
        parser.add_argument(
            "--template_path",
            type=str,
            required=True,
            help="Path to the email template",
        )
        parser.add_argument(
            "--players",
            help="Send to players",
            action="store_true",
        )
        parser.add_argument("--coaches", help="Send to coaches", action="store_true")
        parser.add_argument("--scouts", help="Send to scouts", action="store_true")
        parser.add_argument("--clubs", help="Send to clubs", action="store_true")
        parser.add_argument("--guests", help="Send to guests", action="store_true")
        parser.add_argument("--managers", help="Send to managers", action="store_true")
        parser.add_argument("--all", help="Send to all", action="store_true")
        parser.add_argument(
            "--others", help="Additional email recipients", type=str, default=""
        )

    def _parse_others_recipients(self) -> Set[str]:
        """
        Parse the `--others` argument to get a list of additional email addresses.
        """
        if not self.args.others:
            return set()

        return {email.strip() for email in self.args.others.split(";") if email.strip()}

    def _get_recipients(self) -> List[str]:
        """
        Get recipients based on command arguments.
        If `--all` is provided, return all profiles.
        """
        recipients = set()

        if self.args.all:
            recipients.update(
                set(ProfileMeta.objects.all().values_list("user__email", flat=True))
            )

        args_mapper = {
            "playerprofile": self.args.players,
            "coachprofile": self.args.coaches,
            "scoutprofile": self.args.scouts,
            "clubprofile": self.args.clubs,
            "guestprofile": self.args.guests,
            "managerprofile": self.args.managers,
        }
        profile_names_to_fetch = [
            key for key, arg_state in args_mapper.items() if arg_state
        ]
        recipients.update(
            set(
                ProfileMeta.objects.filter(
                    _profile_class__in=profile_names_to_fetch
                ).values_list("user__email", flat=True)
            )
        )
        recipients.update(self._parse_others_recipients())

    def _set_args(self, arguments: Dict[str, Any]) -> None:
        """
        Set the command arguments.
        """
        self.args = Args(
            players=arguments["players"],
            coaches=arguments["coaches"],
            scouts=arguments["scouts"],
            clubs=arguments["clubs"],
            guests=arguments["guests"],
            managers=arguments["managers"],
            all=arguments["all"],
            others=arguments["others"],
        )
