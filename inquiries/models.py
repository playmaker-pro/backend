import logging
from datetime import datetime, timedelta
from typing import Optional

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition

from inquiries.errors import ForbiddenLogAction
from inquiries.schemas import InquiryPlanTypeRef as _InquiryPlanTypeRef
from inquiries.signals import (
    inquiry_accepted,
    inquiry_pool_exhausted,
    inquiry_rejected,
    inquiry_reminder,
    inquiry_restored,
    inquiry_sent,
)
from inquiries.utils import InquiryMessageContentParser as _ContentParser
from mailing.models import EmailTemplate as _EmailTemplate
from mailing.schemas import EmailSchema as _EmailSchema
from utils.constants import (
    INQUIRY_CONTACT_URL,
    INQUIRY_LIMIT_INCREASE_URL,
    TRANSFER_MARKET_URL,
)

logger = logging.getLogger("inquiries")


class InquiryLogMessage(models.Model):
    EMAIL_PATTERN = _(
        "Type '#male_form|female_form#' - to mark something that should be determined "
        "by gender (e.g. #Otrzymałeś|Otrzymałaś#).\n"
        "<> - to include user related with log.\n"
        "'#r#' to include user related with log with role.\n"
        "'#rb#' to include user related with log with role in objective case (biernik)."
        "\n"
        "#url# - to include additional url."
    )

    class MessageType(models.TextChoices):
        ACCEPTED = "ACCEPTED_INQUIRY", _("Accepted inquiry")
        REJECTED = "REJECTED_INQUIRY", _("Rejected inquiry")
        NEW = "NEW_INQUIRY", _("New inquiry")
        OUTDATED = "OUTDATED_INQUIRY", _("Outdated inquiry")
        UNDEFINED = "UNDEFINED_INQUIRY", _("Undefined inquiry")
        OUTDATED_REMINDER = "OUTDATED_REMINDER", _("Reminder about outdated inquiry")

    log_body = models.TextField(
        help_text=_(
            "Message should include '<>' as placeholder for user related with log."
        ),
        blank=True,
        null=True,
    )

    email_title = models.TextField(
        help_text=EMAIL_PATTERN,
        blank=True,
        null=True,
    )
    email_body = models.TextField(
        help_text=EMAIL_PATTERN,
        blank=True,
        null=True,
    )
    send_mail = models.BooleanField(
        default=False,
        help_text=_("Should email be sent automatically when log is created?"),
    )

    log_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.UNDEFINED,
        unique=True,
    )

    def __str__(self) -> str:
        return f"{self.log_type}: {self.log_body}"


class UserInquiryLog(models.Model):
    """User Inquiry Log"""

    log_owner = models.ForeignKey(
        "UserInquiry",
        on_delete=models.CASCADE,
        related_name="logs",
    )
    related_with = models.ForeignKey(
        "UserInquiry",
        on_delete=models.CASCADE,
        related_name="related_logs",
    )
    ref = models.ForeignKey(
        "InquiryRequest", on_delete=models.CASCADE, related_name="logs"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    message = models.ForeignKey(
        InquiryLogMessage,
        on_delete=models.PROTECT,
        related_name="logs",
    )

    def __str__(self) -> str:
        return (
            f"{self.log_owner.user} -- "
            f"{self.created_at_readable} -- "
            f"{self.log_message_body}"
        )

    @property
    def created_at_readable(self) -> str:
        """Get created_at in readable format."""
        return self.created_at.strftime("%H:%M, %d.%m.%Y")

    def create_email_schema(self) -> _EmailSchema:
        """Create email schema based on log message and related user."""
        return _EmailSchema(
            body=self.email_body,
            subject=self.email_title,
            recipients=[self.log_owner.user.contact_email],
            type=self.message.log_type,
        )

    def send_email_to_user(self) -> None:
        """Send email to user with new inquiry request state"""
        schema = self.create_email_schema()
        _EmailTemplate.send_email(schema)

    @property
    def log_message_body(self) -> str:
        """Parse message body to include user related with log"""
        return _ContentParser(self).parse_log_body

    @property
    def email_title(self) -> str:
        """Parse email title to include user related with log"""
        return _ContentParser(self).parse_email_title

    @property
    def email_body(self) -> str:
        """Parse email body to include user related with log"""
        return _ContentParser(self, url=self.ulr_to_profile).parse_email_body

    @property
    def ulr_to_profile(self) -> str:
        """Get url to profile based on log type"""
        if self.message.log_type == InquiryLogMessage.MessageType.OUTDATED:
            return TRANSFER_MARKET_URL
        elif self.message.log_type == InquiryLogMessage.MessageType.OUTDATED_REMINDER:
            return INQUIRY_CONTACT_URL
        return ""

    def save(self, *args, **kwargs):
        if self.message.send_mail and self._state.adding:
            self.send_email_to_user()
        super().save(*args, **kwargs)
        logger.info(f"New UserInquiryLog (ID: {self.pk}) created: {self}")


class InquiryPlan(models.Model):
    """Holds information about user's inquiry plans."""

    name = models.CharField(_("Plan Name"), max_length=255, help_text=_("Plan name"))
    limit = models.PositiveIntegerField(
        _("Plan limit"), help_text=_("Limit how many actions are allowed")
    )
    sort = models.PositiveIntegerField(
        ("Soring"),
        default=0,
        help_text=_(
            "Used to sort plans low numbers threaded as lowest plans. Default=0 "
            "which means this is not set."
        ),
    )
    description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
        help_text=_(
            "Short description what is rationale behind plan. Used only for "
            "internal purpose."
        ),
    )
    default = models.BooleanField(
        _("Default Plan"),
        default=False,
        help_text=_(
            "Defines if this is default plan selected during account creation."
        ),
    )
    type_ref = models.CharField(
        max_length=50,
        choices=((ref.value, ref.value) for ref in _InquiryPlanTypeRef),
        null=True,
        blank=True,
        unique=True,
        help_text=_(
            "Defines if this is premium plan and what type of premium plan it is."
        ),
    )

    class Meta:
        unique_together = ("name", "limit")

    def __str__(self):
        return f"{self.name}({self.limit})"

    @classmethod
    def basic(cls) -> "InquiryPlan":
        """Get a basic plan"""
        return cls.objects.get(default=True)

    def save(self, *args, **kwargs):
        if self.default and self is not InquiryPlan.objects.get(default=True):
            raise ValueError("There can be only one default plan.")
        super().save(*args, **kwargs)


class UserInquiry(models.Model):
    class UserInquiryManager(models.Manager):
        def limit_reached(self) -> models.QuerySet:
            """Get users with limit reached"""
            return self.filter(counter_raw__gte=models.F("plan__limit"))

    objects = UserInquiryManager()

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True
    )

    plan = models.ForeignKey(
        InquiryPlan, on_delete=models.SET_NULL, null=True, blank=True
    )

    counter_raw = models.PositiveIntegerField(
        _("Obecna ilość zapytań"),
        default=0,
        help_text=_("Current number of used inquiries."),
    )

    limit_raw = models.PositiveIntegerField(default=2)

    @property
    def limit(self):
        if self.premium_inquiries:
            return self.limit_raw + self.premium_inquiries.INQUIRIES_LIMIT
        return self.limit_raw

    @property
    def counter(self):
        if self.premium_inquiries:
            return self.counter_raw + self.premium_inquiries.current_counter
        return self.counter_raw

    @counter.setter
    def counter(self, value):
        self.counter_raw = value

    @property
    def can_make_request(self):
        return self.counter < self.limit

    @property
    def left(self):
        return self.limit - self.counter

    def reset(self):
        """Reset current counter"""
        self.counter_raw = 0
        self.save()

    def reset_inquiries(self) -> None:
        """
        Set basic plan and reset counter to 0.
        """
        self.plan = InquiryPlan.basic()
        self.counter_raw = 0
        self.limit_raw = self.plan.limit
        self.save()

    @property
    def premium_inquiries_status(self) -> (int, int):
        if pi := self.premium_inquiries:
            return pi.status
        return 0, 0

    @property
    def premium_inquiries(self) -> Optional["premium.models.PremiumInquiriesProduct"]:  # noqa: F821
        if self.user.profile and self.user.profile.has_premium_inquiries:
            premium_inquiries = self.user.profile.premium_products.inquiries
            premium_inquiries.check_refresh()
            return premium_inquiries

    @property
    def regular_pool(self) -> (int, int):
        return self.counter_raw, self.limit_raw

    @property
    def premium_profile_pool(self) -> (int, int):
        if self.premium_inquiries:
            return (
                self.premium_inquiries.current_counter,
                self.premium_inquiries.INQUIRIES_LIMIT,
            )
        return 0, 0

    def increment(self):
        """Increase by one counter"""
        if self.premium_inquiries and self.premium_inquiries.can_use_premium_inquiries:
            self.premium_inquiries.increment_counter()
        else:
            if self.counter < self.limit:
                self.counter_raw += 1
                self.save()
        self.check_limit_to_notify()

    def check_limit_to_notify(self) -> None:
        """Decide user should be notified about reaching the limit"""
        if self.counter == self.limit:
            self.notify_about_limit(force=True)

    def notify_about_limit(self, force: bool = False) -> None:
        """Notify user about reaching the limit"""
        self.mail_about_limit(force_send=force)
        self.notification_about_limit(force_send=force)

    def mail_about_limit(self, force_send: bool = False) -> None:
        """Send email notification about reaching the limit"""
        if (
            _EmailTemplate.objects.can_sent_inquiry_limit_reached_email(self.user)
            or force_send
        ):
            template = _EmailTemplate.objects.inquiry_limit_reached_template()
            email_body = template.body.replace("#url#", INQUIRY_LIMIT_INCREASE_URL)
            schema = _EmailSchema(
                body=email_body,
                subject=template.subject,
                recipients=[self.user.contact_email],
                type=_EmailTemplate.EmailType.INQUIRY_LIMIT,
            )
            _EmailTemplate.send_email(schema)

    def notification_about_limit(self, force_send: bool = False) -> None:
        """Create notification about reaching the limit"""
        inquiry_pool_exhausted.send(
            sender=self.__class__, user=self.user, force=force_send
        )

    def decrement(self):
        """Decrease by one counter"""
        if self.counter > 0:
            self.counter -= 1
            self.save()

    @property
    def get_days_until_next_reference(self) -> int:
        """
        Calculate the number of days remaining until the next reference date.

        The reference dates are May 31st and November 30th of the current year.
        If today's date is on or before May 31st, the reference date is May 31st.
        If today's date is after May 31st, the reference date is November 30th.
        """
        today = datetime.today()
        year = today.year

        # Define reference dates for the current year
        may_31_this_year = datetime(year, 5, 31)
        nov_30_this_year = datetime(year, 11, 30)

        # Determine the next reference date based on the current date
        if today <= may_31_this_year:
            next_reference_date = may_31_this_year
        else:
            next_reference_date = nov_30_this_year

        # Calculate the difference in days until the next reference date
        days_until_next_reference = (next_reference_date - today).days
        return max(days_until_next_reference, 0)

    def set_new_plan(self, plan: InquiryPlan) -> None:
        """Set a new plan for user"""
        self.plan = plan
        self.limit_raw += plan.limit
        self.save(update_fields=["plan", "limit_raw"])

    def __str__(self):
        return f"{self.user}: {self.counter}/{self.limit}"


class InquiryRequestManager(models.Manager):
    def contacts(self, user_instance: settings.AUTH_USER_MODEL) -> models.QuerySet:
        """Query user contacts (accepted requests)"""
        return self.filter(
            models.Q(status=InquiryRequest.STATUS_ACCEPTED)
            & (models.Q(sender=user_instance) | models.Q(recipient=user_instance))
        )

    def outdated_for_sender(self) -> models.QuerySet:
        """
        Filter unread InquiryRequest that are older than week
        """
        week_ago = timezone.now() - timedelta(days=7)
        return self.filter(status=InquiryRequest.STATUS_SENT, created_at__lte=week_ago)

    def to_notify_sender_about_outdated(self) -> models.QuerySet:
        """Filter outdated InquiryRequest have not been logged yet."""
        return self.outdated_for_sender().exclude(
            logs__message__log_type=InquiryLogMessage.MessageType.OUTDATED
        )

    def to_remind_recipient_about_outdated(self) -> models.QuerySet:
        """
        Filter InquiryRequest in conditions:
        - older than 3 days and no reminder logs created
        - older than 6 days and only 1 reminder log created

        Queries are that complicated because we want to ensure that user won't get spam.
        """
        curr_date = timezone.now()
        _3_days = curr_date - timedelta(days=3)
        _6_days = curr_date - timedelta(days=6)

        # older than 3 days and no reminder logs created
        _3_days_qs = self.filter(
            status=InquiryRequest.STATUS_SENT, created_at__lte=_3_days
        ).exclude(
            logs__message__log_type=InquiryLogMessage.MessageType.OUTDATED_REMINDER
        )

        # older than 6 days and only 1 reminder log created
        _6_days_qs = (
            self.filter(status=InquiryRequest.STATUS_SENT, created_at__lte=_6_days)
            .alias(
                reminder_count=models.Count(
                    models.Case(
                        models.When(
                            logs__message__log_type=InquiryLogMessage.MessageType.OUTDATED_REMINDER,  # noqa: E501
                            then=1,
                        ),
                        output_field=models.IntegerField(),
                    )
                )
            )
            .filter(reminder_count=1)
        )

        return _3_days_qs.union(_6_days_qs)  # concat querysets without duplicates


class InquiryRequest(models.Model):
    objects = InquiryRequestManager()

    STATUS_NEW = "NOWE"
    STATUS_SENT = "WYSŁANO"
    STATUS_RECEIVED = "PRZECZYTANE"
    STATUS_ACCEPTED = "ZAAKCEPTOWANE"
    STATUS_REJECTED = "ODRZUCONE"
    UNSEEN_STATES = [STATUS_SENT]
    ACTIVE_STATES = [STATUS_NEW, STATUS_SENT, STATUS_RECEIVED]
    RESOLVED_STATES = [STATUS_ACCEPTED, STATUS_REJECTED]

    STATUS_CHOICES = (
        (STATUS_NEW, STATUS_NEW),
        (STATUS_SENT, STATUS_SENT),
        (STATUS_RECEIVED, STATUS_RECEIVED),
        (STATUS_ACCEPTED, STATUS_ACCEPTED),
        (STATUS_REJECTED, STATUS_REJECTED),
    )

    status = FSMField(default=STATUS_NEW, choices=STATUS_CHOICES)

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="sender_request_recipient",
        on_delete=models.CASCADE,
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="inquiry_request_recipient",
        on_delete=models.CASCADE,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_read_by_sender = models.BooleanField(default=False)
    is_read_by_recipient = models.BooleanField(default=False)

    def create_log_for_sender(self, log_type: InquiryLogMessage.MessageType) -> None:
        """Create log for sender"""
        message = InquiryLogMessage.objects.get(log_type=log_type)
        UserInquiryLog.objects.create(
            log_owner=self.sender.userinquiry,
            related_with=self.recipient.userinquiry,
            message=message,
            ref=self,
        )

    def create_log_for_recipient(self, log_type: InquiryLogMessage.MessageType) -> None:
        """Create log for recipient"""
        message = InquiryLogMessage.objects.get(log_type=log_type)
        UserInquiryLog.objects.create(
            log_owner=self.recipient.userinquiry,
            related_with=self.sender.userinquiry,
            message=message,
            ref=self,
        )

    def is_active(self):
        return self.status in self.ACTIVE_STATES

    def is_resolved(self):
        return self.status in self.RESOLVED_STATES

    def status_display_for(self, user):
        status_map = {}
        if user == self.recipient:
            status_map = {"WYSŁANO": "OTRZYMANO"}
        return status_map.get(self.status, self.status)

    @transition(field=status, source=[STATUS_NEW], target=STATUS_SENT)
    def send(self):
        """Should be appeared when message was distributed to recipient"""

    @transition(field=status, source=[STATUS_SENT], target=STATUS_RECEIVED)
    def read(self):
        """Should be appeared when message readed/seen by recipient"""
        logger.info(
            f"{self.recipient} read request from {self.sender}. -- "
            f"InquiryRequestID: {self.pk}"
        )
        self.is_read_by_sender = False

    @transition(
        field=status,
        source=ACTIVE_STATES,
        target=STATUS_ACCEPTED,
    )
    def accept(self) -> None:
        """Should be appeared when message was accepted by recipient"""

        logger.debug(
            f"#{self.pk} reuqest accepted creating sender and recipient contanct body"
        )
        self.create_log_for_sender(InquiryLogMessage.MessageType.ACCEPTED)
        logger.info(
            f"{self.recipient} accepted request from {self.sender}. -- "
            f"InquiryRequestID: {self.pk}"
        )
        inquiry_accepted.send(sender=self.__class__, inquiry_request=self)
        self.is_read_by_sender = False

    @transition(
        field=status,
        source=ACTIVE_STATES,
        target=STATUS_REJECTED,
    )
    def reject(self) -> None:
        """Should be appeared when message was rejected by recipient"""

        self.create_log_for_sender(InquiryLogMessage.MessageType.REJECTED)
        logger.info(
            f"{self.recipient} rejected request from {self.sender}. -- "
            f"InquiryRequestID: {self.pk}"
        )
        inquiry_rejected.send(sender=self.__class__, inquiry_request=self)
        self.is_read_by_sender = False

    def save(self, *args, **kwargs):
        recipient_profile_uuid = kwargs.pop("recipient_profile_uuid", None)
        self._recipient_profile_uuid = recipient_profile_uuid
        adding = self._state.adding

        if self.status == self.STATUS_NEW:
            self.send()

        super().save(*args, **kwargs)
        if recipient_profile_uuid:
            inquiry_sent.send(
                sender=self.__class__,
                inquiry_request=self,
                profile_uuid=recipient_profile_uuid,
            )

        if adding:
            self.sender.userinquiry.increment()  # type: ignore
            self.create_log_for_recipient(
                InquiryLogMessage.MessageType.NEW,
            )
            logger.info(
                f"{self.sender} sent request to {self.recipient}. -- "
                f"InquiryRequestID: {self.pk}"
            )

    def reward_sender(self) -> None:
        """Reward sender if request is outdated. Create log for sender."""
        if not self.can_be_rewarded:
            raise ForbiddenLogAction("Cannot reward sender anymore.")

        self.sender.userinquiry.decrement()
        inquiry_restored.send(sender=self.__class__, inquiry_request=self)
        self.create_log_for_sender(InquiryLogMessage.MessageType.OUTDATED)

    def notify_recipient_about_outdated(self) -> None:
        """
        Create log for recipient that request require action.
        Raise ForbiddenLogAction if recipient cannot be reminded anymore.
        """
        if not self.can_be_reminded:
            raise ForbiddenLogAction("Cannot create more than 2 reminders.")
        inquiry_reminder.send(sender=self.__class__, inquiry_request=self)
        self.create_log_for_recipient(InquiryLogMessage.MessageType.OUTDATED_REMINDER)

    @property
    def can_be_reminded(self) -> bool:
        """Check if request recipient can be reminded"""
        return self in self.__class__.objects.to_remind_recipient_about_outdated()

    @property
    def can_be_rewarded(self) -> bool:
        """Check if request sender can be rewarded"""
        return self in self.__class__.objects.to_notify_sender_about_outdated()

    def __str__(self):
        return f"{self.sender} --({self.status})-> {self.recipient}"
