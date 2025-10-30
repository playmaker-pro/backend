import logging
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Set

from django.core.management.base import BaseCommand
from django.db.models import QuerySet

from mailing.schemas import MailContent, MailingPreferenceType
from mailing.services import MailingService
from mailing.utils import build_email_context
from profiles.models import ProfileMeta
from users.models import User

logger = logging.getLogger("commands")


@dataclass
class Args:
    """
    Dataclass to hold command arguments.
    """

    title: str
    template_path: str
    players: bool
    coaches: bool
    scouts: bool
    clubs: bool
    guests: bool
    managers: bool
    all: bool
    others: str  # Comma-separated list of additional email addresses


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
        recipients: QuerySet[User] = self._get_recipients()
        others: Set[str] = self._parse_others_recipients()
        if not (recipients or others):
            self.stdout.write(self.style.WARNING("No recipients found."))
            return
        operation_id = uuid.uuid4()

        for recipient_user in recipients:
            try:
                schema = MailContent(
                    subject_format=self.args.title,
                    template_file=self.args.template_path,
                    mailing_type=MailingPreferenceType.MARKETING.value,
                )
                context = build_email_context(
                    user=recipient_user,
                    mailing_type=schema.mailing_type,
                )
                MailingService(schema(context), operation_id).send_mail(recipient_user)
            except Exception as e:
                logger.error(f"Error preparing email for {recipient_user.email}: {e}")
                self.stdout.write(
                    self.style.ERROR(
                        f"Error preparing email for {recipient_user.email}: {e}"
                    )
                )
                continue

        for other_email in others:
            content = MailContent(
                subject_format=self.args.title,
                template_file=self.args.template_path,
            )
            MailingService(content(), operation_id).send_email_to_non_user(other_email)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully queued emails for {len(recipients)} recipients"
            )
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

    def _get_recipients(self) -> QuerySet[ProfileMeta]:
        """
        Get recipients based on command arguments.
        If `--all` is provided, return all profiles.
        """
        if self.args.all:
            return User.objects.filter(
                mailing__preferences__marketing=True,
                is_email_verified=True,
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
        return User.objects.filter(
            metas___profile_class__in=profile_names_to_fetch,
            mailing__preferences__marketing=True,
            is_email_verified=True,
        ).distinct()

    def _set_args(self, arguments: Dict[str, Any]) -> None:
        """
        Set the command arguments.
        """
        self.args = Args(
            title=arguments["title"],
            template_path=arguments["template_path"],
            players=arguments["players"],
            coaches=arguments["coaches"],
            scouts=arguments["scouts"],
            clubs=arguments["clubs"],
            guests=arguments["guests"],
            managers=arguments["managers"],
            all=arguments["all"],
            others=arguments["others"],
        )
