import logging

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition

from inquiries.plans import basic_plan, premium_plan
from notifications.mail import request_accepted, request_declined, request_new

logger = logging.getLogger(__name__)


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
            "Used to sort plans low numbers threaded as lowest plans. Default=0 which means this is not set."
        ),
    )

    description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
        help_text=_(
            "Short description what is rationale behind plan. Used only for internal purpose."
        ),
    )

    default = models.BooleanField(
        _("Default Plan"),
        default=False,
        help_text=_(
            "Defines if this is default plan selected during account creation."
        ),
    )

    class Meta:
        unique_together = ("name", "limit")

    def __str__(self):
        return f"{self.name}({self.limit})"

    @classmethod
    def basic(cls) -> "InquiryPlan":
        """Get basic plan"""
        return cls.objects.get_or_create(**basic_plan.dict())[0]

    @classmethod
    def premium(cls) -> "InquiryPlan":
        """Get premium plan"""
        return cls.objects.get_or_create(**premium_plan.dict())[0]


class UserInquiry(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True
    )

    plan = models.ForeignKey(InquiryPlan, on_delete=models.CASCADE)

    counter = models.PositiveIntegerField(
        _("Obecna ilość zapytań"),
        default=0,
        help_text=_("Current number of used inquiries."),
    )

    @property
    def can_make_request(self):
        return self.counter < self.limit

    @property
    def left(self):
        return self.plan.limit - self.counter

    @property
    def limit(self):
        return self.plan.limit

    def reset(self):
        """Reset current counter"""
        self.counter = 0
        self.save()

    def increment(self):
        """Increase by one counter"""
        self.counter += 1
        self.save()

    def __str__(self):
        return f"{self.user}: {self.counter}/{self.plan.limit}"


class InquiryRequestManager(models.Manager):
    def contacts(self, user_instance: settings.AUTH_USER_MODEL) -> models.QuerySet:
        """Query user contacts (accepted requests)"""
        return self.filter(
            models.Q(status=InquiryRequest.STATUS_ACCEPTED)
            & (models.Q(sender=user_instance) | models.Q(recipient=user_instance))
        )


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

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    # content = models.JSONField(null=True, blank=True)

    body = models.TextField(null=True, blank=True)

    body_recipient = models.TextField(null=True, blank=True)

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
        request_new(self)

    @transition(field=status, source=[STATUS_SENT], target=STATUS_RECEIVED)
    def read(self):
        """Should be appeared when message readed/seen by recipient"""

    @transition(
        field=status,
        source=[STATUS_NEW, STATUS_SENT, STATUS_RECEIVED],
        target=STATUS_ACCEPTED,
    )
    def accept(self) -> None:
        """Should be appeared when message was accepted by recipient"""
        logger.debug(
            f"#{self.pk} reuqest accepted creating sender and recipient contanct body"
        )
        self.set_bodies()
        request_accepted(self)

    @transition(
        field=status,
        source=[STATUS_NEW, STATUS_SENT, STATUS_RECEIVED],
        target=STATUS_REJECTED,
    )
    def reject(self) -> None:
        """Should be appeared when message was rejected by recipient"""
        request_declined(self)

    def save(self, *args, **kwargs):
        if self.status == self.STATUS_NEW:
            self.send()  # @todo due to problem with detecting changes of paramters here is hax to alter status to send, durgin which message is sedn via mail
        if self._state.adding:
            self.sender.userinquiry.increment()  # type: ignore
        super().save(*args, **kwargs)

    def set_bodies(self) -> None:
        """Set contact bodies for inquire request"""
        self.body = self.sender.inquiry_contact.contact_body  # type: ignore
        self.body_recipient = self.recipient.inquiry_contact.contact_body  # type: ignore
        super().save(update_fields=["body", "body_recipient"])

    def __str__(self):
        return f"{self.sender} --({self.status})-> {self.recipient}"


class InquiryContact(models.Model):
    phone = models.CharField(_("Numer telefonu"), max_length=15, blank=True, null=True)
    email = models.EmailField(_("Email"), max_length=100, blank=True, null=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="inquiry_contact",
    )

    @property
    def _phone(self) -> str:
        """Get phone number"""
        return self.phone  # type: ignore

    @property
    def _email(self) -> str:
        """Get email"""
        return self.email or self.user.email  # type: ignore

    @_email.setter
    def _email(self, value: str) -> None:
        """Set email"""
        self.email = value

    @property
    def contact_body(self) -> str:
        """Get text-based contact body"""
        return (
            f"{_('Numer telefonu')}: {self._phone or '-'} / "
            f"{_('Email')}: {self._email}"
        )

    @classmethod
    def parse_custom_body(cls, phone: str, email: str) -> str:
        """Parse custom body"""
        dummy_contact = cls(phone=phone, email=email)
        return dummy_contact.contact_body

    def __str__(self) -> str:
        return f"{self.user} -- {self.contact_body}"
