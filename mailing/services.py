from django.db.models import Count, F, Q
from django.utils import timezone

from mailing.schemas import EmailTemplateRegistry, Envelope, MailContent
from mailing.utils import build_email_context
from premium.models import PremiumProduct
from profiles.models import ClubProfile, CoachProfile, PlayerProfile, ProfileMeta
from users.models import User


class MailingService:
    """Handles sending templated emails and optionally logging them in the outbox."""

    def __init__(self, schema: MailContent) -> None:
        """
        Initialize the mailing service.

        Args:
            schema (MailContent): The email template schema to use.
        """
        if schema is None:
            raise ValueError("Schema cannot be None")
        self._schema = schema

    def send_mail(self, recipient: User) -> None:
        """
        Send the email using the provided schema and recipient.
        """
        envelope = Envelope(mail=self._schema, recipients=[recipient.email])
        envelope.send()

    def send_mail_to_admins(self) -> None:
        """
        Send the email to admins using the provided schema.
        """
        envelope = Envelope(mail=self._schema)
        envelope.send_to_admins()


class PostmanService:
    def blank_profile(self):
        """
        Check for profiles that are not filled out and notify the user.
        """
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        mail_schema = EmailTemplateRegistry.INCOMPLETE_PROFILE_REMINDER

        for profile in (
            PlayerProfile.objects.filter(user__declared_role="P")
            .filter(
                Q(team_object__isnull=True)
                | Q(user__user_video__isnull=True)
                | Q(user__display_status=User.DisplayStatus.NOT_SHOWN)
            )
            .exclude(
                user__mailing__mailbox__sent_at__gt=thirty_days_ago,
                user__mailing__mailbox__mail_template=mail_schema.template_file,
            )
            .exclude(
                user__date_joined__gt=timezone.now() - timezone.timedelta(days=3)
            )
        ).select_related("user"):
            context = build_email_context(profile.user)
            MailingService(mail_schema(context)).send_mail(profile.user)

        for profile in (
            CoachProfile.objects.filter(
                user__declared_role="T",
                user__display_status=User.DisplayStatus.NOT_SHOWN,
            )
            .exclude(
                user__mailing__mailbox__sent_at__gt=thirty_days_ago,
                user__mailing__mailbox__mail_template=mail_schema.template_file,
            )
            .exclude(
                user__date_joined__gt=timezone.now() - timezone.timedelta(days=3)
            )
            .select_related("user")
        ):
            context = build_email_context(profile.user)
            MailingService(mail_schema(context)).send_mail(profile.user)

        for profile in (
            ClubProfile.objects.filter(
                user__declared_role="C",
                user__display_status=User.DisplayStatus.NOT_SHOWN,
            )
            .exclude(
                user__mailing__mailbox__sent_at__gt=thirty_days_ago,
                user__mailing__mailbox__mail_template=mail_schema.template_file,
            )
            .exclude(
                user__date_joined__gt=timezone.now() - timezone.timedelta(days=3)
            )
            .select_related("user")
        ):
            context = build_email_context(profile.user)
            MailingService(mail_schema(context)).send_mail(profile.user)

    def inactive_for_30_days(self):
        """
        Check for profiles that have been inactive for 30 days and notify the user.
        """
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        mail_schema = EmailTemplateRegistry.INACTIVE_USER_REMINDER

        for user in (
            User.objects.filter(
                last_activity__lt=thirty_days_ago,
            )
            .exclude(
                mailing__mailbox__sent_at__gt=thirty_days_ago,
                mailing__mailbox__mail_template=mail_schema.template_file,
            )
            .exclude(
                mailing__mailbox__sent_at__gt=F("last_activity"),
                mailing__mailbox__mail_template=mail_schema.template_file,
            )
        ):
            context = build_email_context(user, days_inactive=30)
            MailingService(mail_schema(context)).send_mail(user)

    def inactive_for_90_days(self):
        """
        Check for profiles that have been inactive for 90 days and notify the user.
        """
        ninety_days_ago = timezone.now() - timezone.timedelta(days=90)
        mail_schema = EmailTemplateRegistry.INACTIVE_USER_REMINDER

        for user in (
            User.objects.filter(
                last_activity__lt=ninety_days_ago,
            )
            .exclude(
                mailing__mailbox__sent_at__gt=ninety_days_ago,
                mailing__mailbox__mail_template=mail_schema.template_file,
            )
            .exclude(
                mailing__mailbox__sent_at__gt=F("last_activity"),
                mailing__mailbox__mail_template=mail_schema.template_file,
            )
        ):
            context = build_email_context(user, days_inactive=90)
            MailingService(mail_schema(context)).send_mail(user)

    def go_premium(self):
        """
        Remind users to go premium if they haven't done it yet.
        """
        mail_schema = EmailTemplateRegistry.PREMIUM_ENCOURAGEMENT

        for pp in (
            PremiumProduct.objects.filter(premium__valid_until__isnull=True)
            .exclude(user__isnull=True)
            .exclude(
                user__mailing__mailbox__sent_at__gt=timezone.now()
                - timezone.timedelta(days=30),
                user__mailing__mailbox__mail_template=mail_schema.template_file,
            )
            .exclude(
                user__date_joined__gt=timezone.now() - timezone.timedelta(days=5)
            )
            .select_related("user")
        ):
            context = build_email_context(pp.user)
            MailingService(mail_schema(context)).send_mail(pp.user)

    def views_monthly(
        self,
    ):
        """
        Remind to buy premium after the trial ends.
        """
        mail_schema = EmailTemplateRegistry.PROFILE_VIEWS_MILESTONE

        for meta in (
            ProfileMeta.objects.annotate(
                visits_count=Count(
                    "visited_objects",
                    filter=Q(
                        visited_objects__timestamp__gte=timezone.now()
                        - timezone.timedelta(days=14)
                    ),
                )
            )
            .filter(visits_count__gte=5)
            .exclude(
                user__mailing__mailbox__sent_at__gt=timezone.now()
                - timezone.timedelta(days=14),
                user__mailing__mailbox__mail_template=mail_schema.template_file,
            )
            .select_related("user")
        ):
            context = build_email_context(meta.user)
            MailingService(mail_schema(context)).send_mail(meta.user)

    def player_without_transfer_status(self):
        """
        Notify players without transfer status to update it.
        """
        mail_schema = EmailTemplateRegistry.TRANSFER_STATUS_REMINDER

        for player in (
            PlayerProfile.objects.filter(
                meta__transfer_status__isnull=True,
                user__declared_role="P",
            )
            .exclude(
                user__mailing__mailbox__sent_at__gt=timezone.now()
                - timezone.timedelta(days=60),
                user__mailing__mailbox__mail_template=mail_schema.template_file,
            )
            .exclude(
                user__date_joined__gt=timezone.now() - timezone.timedelta(days=7)
            )
            .select_related("user")
        ):
            context = build_email_context(player.user)
            MailingService(mail_schema(context)).send_mail(player.user)

    def profile_without_transfer_request(self):
        """
        Notify profiles without transfer request to create one.
        """
        mail_schema = EmailTemplateRegistry.TRANSFER_REQUEST_REMINDER

        for meta in (
            ProfileMeta.objects.filter(
                transfer_request__isnull=True,
                user__declared_role__in=["C", "T"],
            )
            .exclude(
                user__mailing__mailbox__sent_at__gt=timezone.now()
                - timezone.timedelta(days=60),
                user__mailing__mailbox__mail_template=mail_schema.template_file,
            )
            .exclude(
                user__date_joined__gt=timezone.now() - timezone.timedelta(days=7)
            )
            .select_related("user")
        ):
            context = build_email_context(meta.user)
            MailingService(mail_schema(context)).send_mail(meta.user)

    def invite_friends(self):
        """
        Invite friends to join the platform.
        """
        mail_schema = EmailTemplateRegistry.INVITE_FRIENDS_REMINDER

        for user in User.objects.exclude(
            mailing__mailbox__sent_at__gt=timezone.now() - timezone.timedelta(days=60),
            mailing__mailbox__mail_template=mail_schema.template_file,
        ).exclude(
            date_joined__gt=timezone.now() - timezone.timedelta(days=10)
        ):
            context = build_email_context(user)
            MailingService(mail_schema(context)).send_mail(user)
