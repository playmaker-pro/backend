from dataclasses import dataclass
from typing import Any, Dict, List

from django.core.management.base import BaseCommand
from django.db.models import QuerySet

from notifications.templates import NotificationBody
from profiles.models import ProfileMeta
from profiles.services import NotificationService


@dataclass
class Args:
    """
    Dataclass to hold command arguments.
    """

    body: NotificationBody

    players: bool = False
    coaches: bool = False
    scouts: bool = False
    clubs: bool = False
    guests: bool = False
    managers: bool = False
    all: bool = False


class Command(BaseCommand):
    """
    Command to send custom notifications to users.
    """

    help = "Send custom notifications to users"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.args: Args = None

    def handle(self, *args, **options):
        self._set_args(options)
        queryset = self._get_queryset()
        success = failed = 0

        for meta in queryset:
            try:
                NotificationService(meta).create_notification(self.args.body)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to send notification to {meta.profile}: {str(e)}"
                    )
                )
                failed += 1
                continue

            self.stdout.write(
                self.style.SUCCESS(
                    f"Notifications sent successfully to {meta.profile}."
                )
            )
            success += 1

        self.stdout.write(
            f"SUCCESS: {success}, FAILED: {failed}, TOTAL: {success + failed}"
        )

    def add_arguments(self, parser):
        parser.add_argument(
            "--title",
            type=str,
            required=True,
            help="Title of the notification",
        )
        parser.add_argument(
            "--description",
            type=str,
            required=True,
            help="Description of the notification",
        )
        parser.add_argument(
            "--href",
            type=str,
            default="",
            help="Link associated with the notification",
        )
        parser.add_argument(
            "--icon",
            type=str,
            default="",
            help="Icon name associated with the notification",
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

    def _get_queryset(self) -> List[QuerySet]:
        """
        Get querysets of profiles based on the command arguments.
        If `--all` is provided, return all profiles.
        """
        if self.args.all:
            return ProfileMeta.objects.all()

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
        return ProfileMeta.objects.filter(_profile_class__in=profile_names_to_fetch)

    def _set_args(self, arguments: Dict[str, Any]) -> None:
        """
        Set the command arguments.
        """
        self.args = Args(
            body=NotificationBody(
                title=arguments["title"],
                description=arguments["description"],
                href=arguments["href"],
                icon=arguments["icon"],
            ),
            players=arguments["players"],
            coaches=arguments["coaches"],
            scouts=arguments["scouts"],
            clubs=arguments["clubs"],
            guests=arguments["guests"],
            managers=arguments["managers"],
            all=arguments["all"],
        )
