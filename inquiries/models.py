import logging
from datetime import datetime, timedelta
from typing import Optional

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition

from inquiries.constants import EMAIL_ENABLED_LOG_TYPES, InquiryLogType
from inquiries.errors import ForbiddenLogAction
from inquiries.schemas import InquiryPlanTypeRef as _InquiryPlanTypeRef
from profiles.services import NotificationService
from utils.constants import (
    INQUIRY_CONTACT_URL,
    TRANSFER_MARKET_URL,
)

logger = logging.getLogger("inquiries")


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
    log_type = models.CharField(
        max_length=20,
        choices=InquiryLogType.choices,
        default=InquiryLogType.UNDEFINED,
    )

    def __str__(self) -> str:
        return f"{self.log_owner.user} -- {self.created_at_readable} -- "

    @property
    def created_at_readable(self) -> str:
        """Get created_at in readable format."""
        return self.created_at.strftime("%H:%M, %d.%m.%Y")

    @property
    def send_mail(self) -> bool:
        """Determine if email should be sent for this log type."""
        return self.log_type in EMAIL_ENABLED_LOG_TYPES

    @property
    def url_to_profile(self) -> str:
        """Get url to profile based on log type"""
        if self.log_type == InquiryLogType.OUTDATED:
            return TRANSFER_MARKET_URL
        elif self.log_type == InquiryLogType.OUTDATED_REMINDER:
            return INQUIRY_CONTACT_URL
        return ""


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
    _default_limit = 2

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
    limit_raw = models.PositiveIntegerField(default=_default_limit)
    _last_limit_notification = models.DateTimeField(
        null=True,
        blank=True,
        default=None,
    )

    @property
    def limit(self):
        if self.premium_inquiries:
            return self.limit_raw + self.premium_inquiries.INQUIRIES_LIMIT
        return self.limit_raw

    @property
    def limit_to_show(self) -> int:
        return (
            self._default_limit + self.premium_inquiries.INQUIRIES_LIMIT
            if self.premium_inquiries
            else self._default_limit
        )

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

    @property
    def left_to_show(self):
        return self.limit - self.counter

    def update_last_limit_notification(self):
        """Update last limit notification date"""
        self._last_limit_notification = timezone.now()
        self.save(update_fields=["_last_limit_notification"])

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

    def reset_plan(self):
        self.plan = InquiryPlan.basic()
        self.limit_raw = self.plan.limit

        if self.counter_raw >= self.limit_raw:
            self.counter_raw = self.limit_raw

        self.save()

    @property
    def premium_inquiries(self) -> Optional["premium.models.PremiumInquiriesProduct"]:  # noqa: F821
        if self.user.profile:
            if self.user.profile.has_premium_inquiries:
                premium_inquiries = self.user.profile.products.inquiries
                premium_inquiries.check_refresh()
                return premium_inquiries
            elif not self.plan or not self.plan.default:
                self.reset_plan()

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
        if self.counter_raw < self.limit_raw:
            self.counter_raw += 1
            self.save()
        else:
            if (
                self.premium_inquiries
                and self.premium_inquiries.can_use_premium_inquiries
            ):
                self.premium_inquiries.increment_counter()

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

    def can_sent_inquiry_limit_reached_email(self) -> bool:
        """
        Return True if user can receive inquiry limit reached email.

        Send email once per round. So:
        - if last email was sent in april current year, we can sent next email after june current year.
        - if last email was sent in july current year, we can sent next email after december current year.
        - if last email was sent in december last year, we can sent next email after june current year.
        """
        curr_date = timezone.now()
        last_sent_mail = self._last_limit_notification
        if not (last_sent_mail):
            return True
        if last_sent_mail.month < 6:
            # last_sent | current_date | result
            # 2023-04-01 | 2023-06-01 | True
            # 2023-04-01 | 2023-05-01 | False
            # 2023-04-01 | 2025-04-01 | True
            return (
                True
                if (curr_date.month >= 6 and curr_date.year >= last_sent_mail.year)
                or curr_date.year > last_sent_mail.year + 1
                else False
            )
        elif last_sent_mail.month == 12:
            # last_sent | current_date | result
            # 2022-12-03 | 2023-06-01 | True
            # 2022-12-03 | 2024-04-01 | True
            # 2022-12-03 | 2023-04-01 | False
            return (
                True
                if (curr_date.month >= 6 and curr_date.year > last_sent_mail.year)
                or curr_date.year > last_sent_mail.year + 1
                else False
            )
        elif last_sent_mail.month >= 6:
            # last_sent | current_date | result
            # 2023-06-01 | 2023-12-01 | True
            # 2023-07-01 | 2023-11-01 | False
            # 2023-07-01 | 2025-11-01 | True
            return (
                True
                if curr_date.month == 12 or curr_date.year > last_sent_mail.year
                else False
            )

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
            logs__log_type=InquiryLogType.OUTDATED
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
        ).exclude(logs__log_type=InquiryLogType.OUTDATED_REMINDER)

        # older than 6 days and only 1 reminder log created
        _6_days_qs = (
            self.filter(status=InquiryRequest.STATUS_SENT, created_at__lte=_6_days)
            .alias(
                reminder_count=models.Count(
                    models.Case(
                        models.When(
                            logs__log_type=InquiryLogType.OUTDATED_REMINDER,  # noqa: E501
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

    anonymous_recipient = models.BooleanField(default=False)

    def create_log_for_sender(self, log_type: InquiryLogType) -> None:
        """Create log for sender"""
        UserInquiryLog.objects.create(
            log_owner=self.sender.userinquiry,
            related_with=self.recipient.userinquiry,
            log_type=log_type,
            ref=self,
        )

    def create_log_for_recipient(self, log_type: InquiryLogType) -> None:
        """Create log for recipient"""
        UserInquiryLog.objects.create(
            log_owner=self.recipient.userinquiry,
            related_with=self.sender.userinquiry,
            log_type=log_type,
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

        NotificationService(self.recipient.profile.meta).notify_new_inquiry(
            self.sender.profile
        )

    @transition(field=status, source=[STATUS_SENT], target=STATUS_RECEIVED)
    def read(self):
        """Should be appeared when message readed/seen by recipient"""

        NotificationService(self.sender.profile.meta).notify_inquiry_read(
            self.recipient.profile, hide_profile=self.anonymous_recipient
        )
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

        logger.info(
            f"{self.recipient} accepted request from {self.sender}. -- "
            f"InquiryRequestID: {self.pk}"
        )
        self.is_read_by_sender = False

        NotificationService(self.sender.profile.meta).notify_inquiry_accepted(
            self.recipient.profile
        )
        self.create_log_for_sender(InquiryLogType.ACCEPTED)

    @transition(
        field=status,
        source=ACTIVE_STATES,
        target=STATUS_REJECTED,
    )
    def reject(self) -> None:
        """Should be appeared when message was rejected by recipient"""

        logger.info(
            f"{self.recipient} rejected request from {self.sender}. -- "
            f"InquiryRequestID: {self.pk}"
        )
        self.is_read_by_sender = False
        NotificationService(self.sender.profile.meta).notify_inquiry_rejected(
            self.recipient.profile, hide_profile=self.anonymous_recipient
        )
        self.create_log_for_sender(InquiryLogType.REJECTED)

    def save(self, *args, **kwargs):
        recipient_profile_uuid = kwargs.pop("recipient_profile_uuid", None)
        self._recipient_profile_uuid = recipient_profile_uuid

        if self.status == self.STATUS_NEW:
            self.send()

        super().save(*args, **kwargs)

    def reward_sender(self) -> None:
        """Reward sender if request is outdated. Create log for sender."""
        if not self.can_be_rewarded:
            raise ForbiddenLogAction("Cannot reward sender anymore.")

        self.sender.userinquiry.decrement()
        self.create_log_for_sender(InquiryLogType.OUTDATED)

    def notify_recipient_about_outdated(self) -> None:
        """
        Create log for recipient that request require action.
        Raise ForbiddenLogAction if recipient cannot be reminded anymore.
        """
        if not self.can_be_reminded:
            raise ForbiddenLogAction("Cannot create more than 2 reminders.")
        self.create_log_for_recipient(InquiryLogType.OUTDATED_REMINDER)

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
