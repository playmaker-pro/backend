import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Count, F, Q
from django.utils import timezone

from mailing.schemas import EmailTemplateRegistry
from mailing.services import MailingService
from premium.models import PremiumProduct
from profiles.models import ClubProfile, CoachProfile, PlayerProfile, ProfileMeta

logger = logging.getLogger("commands")

User = get_user_model()

thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
sixty_days_ago = timezone.now() - timezone.timedelta(days=60)
ninety_days_ago = timezone.now() - timezone.timedelta(days=90)


class Command(BaseCommand):
    help = "Run daily supervisor tasks"

    def handle(self, *args, **options):
        """
        Handle the command to run daily supervisor tasks.
        This includes checking for profiles that need attention.
        """
        try:
            logger.info("Starting daily supervisor tasks")
            self.blank_profile()
            self.inactive_for_30_days()
            self.inactive_for_90_days()
            self.go_premium()
            self.day_after_trial_end()
            self.invite_friends()
            self.views_monthly()
            self.player_without_transfer_status()
            self.profile_without_transfer_request()
            logger.info("Daily supervisor tasks completed successfully")
        except Exception as e:
            logger.error(f"Daily supervisor failed: {e}", exc_info=True)
            raise  # Re-raise to trigger admin notification

    def blank_profile(self):
        """
        Check for profiles that are not filled out and notify the user.
        """
        month_ago = timezone.now() - timezone.timedelta(days=30)
        mail_schema = EmailTemplateRegistry.BLANK_PROFILE()

        for player in (
            PlayerProfile.objects.filter(user__declared_role="P")
            .filter(
                Q(team_object__isnull=True)
                | Q(profile_video__isnull=True)
                | Q(display_status=User.DisplayStatus.NOT_SHOWN)
            )
            .exclude(
                user__mailing__outbox__sent_at__gt=month_ago,
                user__mailing__outbox__mail_template=mail_schema.template_file,
            )
        ):
            MailingService(mail_schema).send_mail(player.user)

        for coach in CoachProfile.objects.filter(
            user__declared_role="T", display_status=User.DisplayStatus.NOT_SHOWN
        ).exclude(
            user__mailing__outbox__sent_at__gt=month_ago,
            user__mailing__outbox__mail_template=mail_schema.template_file,
        ):
            MailingService(mail_schema).send_mail(coach.user)

        for club in ClubProfile.objects.filter(
            user__declared_role="C", display_status=User.DisplayStatus.NOT_SHOWN
        ).exclude(
            user__mailing__outbox__sent_at__gt=month_ago,
            user__mailing__outbox__mail_template=mail_schema.template_file,
        ):
            MailingService(mail_schema).send_mail(club.user)

    def inactive_for_30_days(self):
        """
        Check for profiles that have been inactive for 30 days and notify the user.
        """
        mail_schema = EmailTemplateRegistry.INACTIVE_30_DAYS()

        for user in (
            User.objects.filter(
                last_activity__lt=thirty_days_ago,
            )
            .exclude(
                mailing__outbox__sent_at__gt=thirty_days_ago,
                mailing__outbox__mail_template=mail_schema.template_file,
            )
            .exclude(
                mailing__outbox__sent_at__gt=F("last_activity"),
                mailing__outbox__mail_template=mail_schema.template_file,
            )
        ):
            MailingService(mail_schema).send_mail(user)

    def inactive_for_90_days(self):
        """
        Check for profiles that have been inactive for 90 days and notify the user.
        """
        mail_schema = EmailTemplateRegistry.INACTIVE_90_DAYS()

        for user in (
            User.objects.filter(
                last_activity__lt=ninety_days_ago,
            )
            .exclude(
                mailing__outbox__sent_at__gt=ninety_days_ago,
                mailing__outbox__mail_template=mail_schema.template_file,
            )
            .exclude(
                mailing__outbox__sent_at__gt=F("last_activity"),
                mailing__outbox__mail_template=mail_schema.template_file,
            )
        ):
            MailingService(mail_schema).send_mail(user)

    def go_premium(self):
        """
        Remind users to go premium if they haven't done it yet.
        """
        mail_schema = EmailTemplateRegistry.GO_PREMIUM()

        for user in (
            PremiumProduct.objects.filter(premium__valid_until__isnull=True)
            .exclude(user__isnull=True)
            .exclude(
                mailing__outbox__sent_at__gt=thirty_days_ago,
                mailing__outbox__mail_template=mail_schema.template_file,
            )
            .select_related("user")
        ):
            MailingService(mail_schema).send_mail(user)

    def views_monthly(
        self,
    ):  # ASK: To ma się bindować raz w miesiącu dla gościu co mają +5 wyświetleń w ostatnich 30 dniach?
        """
        Remind to buy premium after the trial ends.
        """
        mail_schema = EmailTemplateRegistry.VIEWS_MONTHLY()

        for user in (
            ProfileMeta.objects.annotate(
                visits_count=Count(
                    "visited_objects",
                    filter=Q(visited_objects__timestamp__gte=thirty_days_ago),
                )
            )
            .filter(visits_count__gt=5)
            .select_related("user")
        ):
            MailingService(mail_schema).send_mail(user)

    def player_without_transfer_status(self):
        """
        Notify players without transfer status to update it.
        """
        mail_schema = EmailTemplateRegistry.PLAYER_WITHOUT_TRANSFER_STATUS()

        for user in (
            PlayerProfile.objects.filter(
                meta__transfer_status__isnull=True,
                user__declared_role="P",
            )
            .exclude(
                user__mailing__outbox__sent_at__gt=sixty_days_ago,
                user__mailing__outbox__mail_template=mail_schema.template_file,
            )
            .select_related("user")
        ):
            MailingService(mail_schema).send_mail(user)

    def profile_without_transfer_request(self):
        """
        Notify profiles without transfer request to create one.
        """
        mail_schema = EmailTemplateRegistry.PROFILE_WITHOUT_TRANSFER_REQUEST()

        for user in (
            ProfileMeta.objects.filter(
                transfer_request__isnull=True,
                user__declared_role__in=["C", "T"],
            )
            .exclude(
                user__mailing__outbox__sent_at__gt=sixty_days_ago,
                user__mailing__outbox__mail_template=mail_schema.template_file,
            )
            .select_related("user")
        ):
            MailingService(mail_schema).send_mail(user)

    def invite_friends(self):
        """
        Invite friends to join the platform.
        """
        mail_schema = EmailTemplateRegistry.INVITE_FRIENDS()

        for user in User.objects.exclude(
            mailing__outbox__sent_at__gt=sixty_days_ago,
            mailing__outbox__mail_template=mail_schema.template_file,
        ):
            MailingService(mail_schema).send_mail(user)
