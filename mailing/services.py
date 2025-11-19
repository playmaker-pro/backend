import logging
import uuid

from django.db.models import Count, F, Q
from django.utils import timezone

from mailing.schemas import EmailTemplateRegistry, Envelope, MailContent
from mailing.utils import build_email_context
from premium.models import PremiumProduct
from profiles.models import ClubProfile, CoachProfile, PlayerProfile, ProfileMeta
from users.models import User

logger = logging.getLogger("mailing")


class MailingService:
    """Handles sending templated emails and optionally logging them in the outbox."""

    def __init__(
        self,
        schema: MailContent,
        operation_id: uuid.UUID = uuid.uuid4(),
    ) -> None:
        """
        Initialize the mailing service.

        Args:
            schema (MailContent): The email template schema to use.
        """
        if schema is None:
            raise ValueError("Schema cannot be None")
        self._schema = schema
        self._operation_id = operation_id

    def send_mail(self, recipient: User) -> None:
        """
        Send the email using the provided schema and recipient.
        """
        if self._schema.mailing_type and not recipient.can_send_email(
            self._schema.mailing_type
        ):
            logger.info(
                f"Skipping sending {self._schema.mailing_type} email of subject '{self._schema.subject}' to {recipient.email} due to user preferences",
            )
            return

        envelope = Envelope(mail=self._schema, recipients=[recipient.email])
        envelope.send(operation_id=self._operation_id)

    def send_email_to_non_user(self, email: str) -> None:
        """
        Send the email to a non-registered user using the provided schema.
        """
        envelope = Envelope(mail=self._schema, recipients=[email])
        envelope.send(operation_id=self._operation_id)

    def send_mail_to_admins(self) -> None:
        """
        Send the email to admins using the provided schema.
        """
        envelope = Envelope(mail=self._schema)
        envelope.send_to_admins()


class PostmanService:
    def __init__(self, logger: logging.Logger = logging.getLogger(__name__)) -> None:
        self.logger = logger

    def blank_profile(self):
        """
        Check for profiles that are not filled out and notify the user.
        """
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        mail_schema = EmailTemplateRegistry.INCOMPLETE_PROFILE_REMINDER
        qs = (
            PlayerProfile.objects.filter(user__declared_role="P")
            .filter(
                Q(team_object__isnull=True)
                | Q(user__user_video__isnull=True)
                | Q(user__display_status=User.DisplayStatus.NOT_SHOWN)
            )
            .exclude(
                user__is_email_verified=False,
            )
            .exclude(
                user__mailing__mailbox__created_at__gt=thirty_days_ago,
                user__mailing__mailbox__mail_template=mail_schema.template_file,
            )
            .exclude(user__date_joined__gt=timezone.now() - timezone.timedelta(days=3))
            .select_related("user")
        )

        counter = 0
        for profile in qs:
            try:
                context = build_email_context(
                    profile.user, mailing_type=mail_schema.mailing_type
                )
                MailingService(mail_schema(context)).send_mail(profile.user)
                self.logger.info(
                    "Sent incomplete profile reminder to %s", profile.user.email
                )
            except Exception as e:
                self.logger.error(
                    "Failed to send incomplete profile reminder to %s: %s",
                    profile.user.email,
                    str(e),
                )
            else:
                counter += 1
        self.logger.info(
            "Incomplete profile reminder email has been sent to %d players", counter
        )

        qs = (
            CoachProfile.objects.filter(
                user__declared_role="T",
                user__display_status=User.DisplayStatus.NOT_SHOWN,
            )
            .exclude(
                user__mailing__mailbox__created_at__gt=thirty_days_ago,
                user__mailing__mailbox__mail_template=mail_schema.template_file,
            )
            .exclude(
                user__is_email_verified=False,
            )
            .exclude(user__date_joined__gt=timezone.now() - timezone.timedelta(days=3))
            .select_related("user")
        )

        counter = 0
        for profile in qs:
            try:
                context = build_email_context(
                    profile.user, mailing_type=mail_schema.mailing_type
                )
                MailingService(mail_schema(context)).send_mail(profile.user)
                self.logger.info(
                    "Sent incomplete profile reminder to %s", profile.user.email
                )
            except Exception as e:
                self.logger.error(
                    "Failed to send incomplete profile reminder to %s: %s",
                    profile.user.email,
                    str(e),
                )
            else:
                counter += 1
        self.logger.info(
            "Incomplete profile reminder email has been sent to %d coaches", counter
        )

        qs = (
            ClubProfile.objects.filter(
                user__declared_role="C",
                user__display_status=User.DisplayStatus.NOT_SHOWN,
            )
            .exclude(
                user__mailing__mailbox__created_at__gt=thirty_days_ago,
                user__mailing__mailbox__mail_template=mail_schema.template_file,
            )
            .exclude(
                user__is_email_verified=False,
            )
            .exclude(user__date_joined__gt=timezone.now() - timezone.timedelta(days=3))
            .select_related("user")
        )
        counter = 0
        for profile in qs:
            try:
                context = build_email_context(
                    profile.user, mailing_type=mail_schema.mailing_type
                )
                MailingService(mail_schema(context)).send_mail(profile.user)
                self.logger.info(
                    "Sent incomplete profile reminder to %s", profile.user.email
                )
            except Exception as e:
                self.logger.error(
                    "Failed to send incomplete profile reminder to %s: %s",
                    profile.user.email,
                    str(e),
                )
            else:
                counter += 1
        self.logger.info(
            "Incomplete profile reminder email has been sent to %d clubs", counter
        )

    def inactive_for_30_days(self):
        """
        Check for profiles that have been inactive for 30 days and notify the user.
        """
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        mail_schema = EmailTemplateRegistry.INACTIVE_USER_REMINDER
        qs = (
            User.objects.filter(
                last_activity__lt=thirty_days_ago,
            )
            .exclude(
                mailing__mailbox__created_at__gt=thirty_days_ago,
                mailing__mailbox__mail_template=mail_schema.template_file,
            )
            .exclude(
                mailing__mailbox__created_at__gt=F("last_activity"),
                mailing__mailbox__mail_template=mail_schema.template_file,
            )
            .exclude(
                is_email_verified=False,
            )
        )
        counter = 0
        for user in qs:
            try:
                context = build_email_context(
                    user, days_inactive=30, mailing_type=mail_schema.mailing_type
                )
                MailingService(mail_schema(context)).send_mail(user)
                self.logger.info("Sent inactive (30 days) user reminder to %s", user.email)
            except Exception as e:
                self.logger.error(
                    "Failed to send inactive (30 days) user reminder to %s: %s",
                    user.email,
                    str(e),
                )
            else:
                counter += 1
        self.logger.info(
            "Inactive (30 days) user reminder email has been sent to %d users",
            counter,
        )

    def inactive_for_90_days(self):
        """
        Check for profiles that have been inactive for 90 days and notify the user.
        """
        ninety_days_ago = timezone.now() - timezone.timedelta(days=90)
        mail_schema = EmailTemplateRegistry.INACTIVE_USER_REMINDER
        qs = (
            User.objects.filter(
                last_activity__lt=ninety_days_ago,
            )
            .exclude(
                mailing__mailbox__created_at__gt=ninety_days_ago,
                mailing__mailbox__mail_template=mail_schema.template_file,
            )
            .exclude(
                mailing__mailbox__created_at__gt=F("last_activity"),
                mailing__mailbox__mail_template=mail_schema.template_file,
            )
            .exclude(
                is_email_verified=False,
            )
        )
        counter = 0
        for user in qs:
            try:
                context = build_email_context(
                    user, days_inactive=90, mailing_type=mail_schema.mailing_type
                )
                MailingService(mail_schema(context)).send_mail(user)
                self.logger.info("Sent inactive (90 days) user reminder to %s", user.email)
            except Exception as e:
                self.logger.error(
                    "Failed to send inactive (90 days) user reminder to %s: %s",
                    user.email,
                    str(e),
                )
            else:
                counter += 1
        self.logger.info(
            "Inactive (90 days) user reminder email has been sent to %d users",
            counter,
        )

    def go_premium(self):
        """
        Remind users to go premium if they haven't done it yet.
        """
        mail_schema = EmailTemplateRegistry.PREMIUM_ENCOURAGEMENT
        qs = (
            PremiumProduct.objects.filter(premium__valid_until__isnull=True)
            .exclude(
                user__mailing__mailbox__created_at__gt=timezone.now()
                - timezone.timedelta(days=30),
                user__mailing__mailbox__mail_template=mail_schema.template_file,
            )
            .exclude(
                user__is_email_verified=False,
            )
            .exclude(user__date_joined__gt=timezone.now() - timezone.timedelta(days=5))
            .select_related("user")
        )
        counter = 0
        for pp in qs:
            try:
                context = build_email_context(
                    pp.user, mailing_type=mail_schema.mailing_type
                )
                MailingService(mail_schema(context)).send_mail(pp.user)
                self.logger.info("Sent premium encouragement email to %s", pp.user.email)
            except Exception as e:
                self.logger.error(
                    "Failed to send premium encouragement email to %s: %s",
                    pp.user.email,
                    str(e),
                )
            else:
                counter += 1
        self.logger.info(
            "Premium encouragement email has been sent to %d users",
            counter,
        )

    def views_monthly(
        self,
    ):
        """
        Remind to buy premium after the trial ends.
        """
        mail_schema = EmailTemplateRegistry.PROFILE_VIEWS_MILESTONE
        qs = (
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
                user__mailing__mailbox__created_at__gt=timezone.now()
                - timezone.timedelta(days=14),
                user__mailing__mailbox__mail_template=mail_schema.template_file,
            )
            .exclude(
                user__is_email_verified=False,
            )
            .select_related("user")
        )
        counter = 0
        for meta in qs:
            try:
                context = build_email_context(
                    meta.user, mailing_type=mail_schema.mailing_type
                )
                MailingService(mail_schema(context)).send_mail(meta.user)
                self.logger.info(
                    "Sent profile views milestone email to %s", meta.user.email
                )
            except Exception as e:
                self.logger.error(
                    "Failed to send profile views milestone email to %s: %s",
                    meta.user.email,
                    str(e),
                )
            else:
                counter += 1
        self.logger.info(
            "Profile views milestone email has been sent to %d users", counter
        )

    def player_without_transfer_status(self):
        """
        Notify players without transfer status to update it.
        """
        mail_schema = EmailTemplateRegistry.TRANSFER_STATUS_REMINDER
        qs = (
            PlayerProfile.objects.filter(
                meta__transfer_status__isnull=True,
                user__declared_role="P",
            )
            .exclude(
                user__mailing__mailbox__created_at__gt=timezone.now()
                - timezone.timedelta(days=60),
                user__mailing__mailbox__mail_template=mail_schema.template_file,
            )
            .exclude(
                user__is_email_verified=False,
            )
            .exclude(user__date_joined__gt=timezone.now() - timezone.timedelta(days=7))
            .select_related("user")
        )
        counter = 0
        for player in qs:
            try:
                context = build_email_context(
                    player.user, mailing_type=mail_schema.mailing_type
                )
                MailingService(mail_schema(context)).send_mail(player.user)
                self.logger.info("Sent transfer status reminder to %s", player.user.email)
            except Exception as e:
                self.logger.error(
                    "Failed to send transfer status reminder to %s: %s",
                    player.user.email,
                    str(e),
                )
            else:
                counter += 1
        self.logger.info(
            "Transfer status reminder email has been sent to %d players", counter
        )

    def profile_without_transfer_request(self):
        """
        Notify profiles without transfer request to create one.
        """
        mail_schema = EmailTemplateRegistry.TRANSFER_REQUEST_REMINDER
        qs = (
            ProfileMeta.objects.filter(
                transfer_request__isnull=True,
                user__declared_role__in=["C", "T"],
            )
            .exclude(
                user__mailing__mailbox__created_at__gt=timezone.now()
                - timezone.timedelta(days=60),
                user__mailing__mailbox__mail_template=mail_schema.template_file,
            )
            .exclude(
                user__is_email_verified=False,
            )
            .exclude(user__date_joined__gt=timezone.now() - timezone.timedelta(days=7))
            .select_related("user")
        )
        counter = 0
        for meta in qs:
            try:
                context = build_email_context(
                    meta.user, mailing_type=mail_schema.mailing_type
                )
                MailingService(mail_schema(context)).send_mail(meta.user)
                self.logger.info("Sent transfer request reminder to %s", meta.user.email)
            except Exception as e:
                self.logger.error(
                    "Failed to send transfer request reminder to %s: %s",
                    meta.user.email,
                    str(e),
                )
            else:
                counter += 1
        self.logger.info(
            "Transfer request reminder email has been sent to %d profiles", counter
        )

    def invite_friends(self):
        """
        Invite friends to join the platform.
        """
        mail_schema = EmailTemplateRegistry.INVITE_FRIENDS_REMINDER
        qs = (
            User.objects.exclude(
                mailing__mailbox__created_at__gt=timezone.now()
                - timezone.timedelta(days=60),
                mailing__mailbox__mail_template=mail_schema.template_file,
            )
            .exclude(
                is_email_verified=False,
            )
            .exclude(date_joined__gt=timezone.now() - timezone.timedelta(days=10))
        )

        counter = 0
        for user in qs:
            try:
                context = build_email_context(user, mailing_type=mail_schema.mailing_type)
                MailingService(mail_schema(context)).send_mail(user)
                self.logger.info("Sent invite friends reminder to %s", user.email)
            except Exception as e:
                self.logger.error(
                    "Failed to send invite friends reminder to %s: %s",
                    user.email,
                    str(e),
                )
            else:
                counter += 1
        self.logger.info(
            "Invite friends reminder email has been sent to %d users", counter
        )
