import logging

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition
from inquiries.utils import InquiryMailManager
from inquiries.utils import TextParser as _TextParser

from inquiries.plans import basic_plan, premium_plan

# from notifications.mail import request_accepted, request_declined, request_new

logger = logging.getLogger(__name__)


class InquiryLogMessage(models.Model):
    class MessageType(models.TextChoices):
        ACCEPTED = "ACCEPTED_INQUIRY", _("Accepted inquiry")
        REJECTED = "REJECTED_INQUIRY", _("Rejected inquiry")
        NEW = "NEW_INQUIRY", _("New inquiry")
        OUTDATED = "OUTDATED_INQUIRY", _("Outdated inquiry")
        UNDEFINED = "UNDEFINED_INQUIRY", _("Undefined inquiry")

    log_body = models.TextField(
        help_text=_(
            "Message should include '<>' as placeholder for user related with log."
        ),
        blank=True,
        null=True,
    )

    email_title = models.TextField(
        help_text=_(
            "Type '#male_form|female_form#' - to mark something that should be determined by gender "
            "(e.g. #Otrzymałeś|Otrzymałaś#). <> - to include user related with log. "
            "'#r#' to include user related with log with role. "
            "'#rb#' to include user related with log with role in objective case (biernik)."
        ),
        blank=True,
        null=True,
    )
    email_body = models.TextField(
        help_text=_(
            "Type '#male_form|female_form#' - to mark something that should be determined by gender "
            "(e.g. #Otrzymałeś|Otrzymałaś#). <> - to include user related with log. "
            "'#r#' to include user related with log with role. "
            "'#rb#' to include user related with log with role in objective case (biernik)."
        ),
        blank=True,
        null=True,
    )
    send_mail = models.BooleanField(
        default=False,
        help_text=_("Should email be sent automatically when log is created?"),
    )

    message_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.UNDEFINED,
        unique=True,
    )

    def __str__(self) -> str:
        return f"{self.message_type}: {self.log_body}"


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
    ref = models.ForeignKey("InquiryRequest", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    message = models.ForeignKey(
        InquiryLogMessage,
        on_delete=models.PROTECT,
        related_name="logs",
    )

    def __str__(self) -> str:
        return f"{self.log_owner.user} ({self.created_at.strftime('%H:%M, %d.%m.%Y')}) -- {self.message.message_type}"

    def save(self, *args, **kwargs):
        """Save instance, send email if configured"""
        if self.message.send_mail and self._state.adding:
            self.send_email_to_user()

        super().save(*args, **kwargs)

    def send_email_to_user(self) -> None:
        """Send email to user with new inquiry request state"""
        InquiryMailManager.send_mail(self)

    @property
    def log_message_body(self) -> str:
        """Parse message body to include user related with log"""
        return _TextParser(self).log_body

    @property
    def email_title(self) -> str:
        """Parse email title to include user related with log"""
        return _TextParser(self).email_title

    @property
    def email_body(self) -> str:
        """Parse email body to include user related with log"""
        return _TextParser(self).email_body


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

    def create_log_for_sender(self, type: InquiryLogMessage.MessageType) -> None:
        """Create log for sender"""
        message = InquiryLogMessage.objects.get(message_type=type)
        UserInquiryLog.objects.create(
            log_owner=self.sender.userinquiry,
            related_with=self.recipient.userinquiry,
            message=message,
            ref=self,
        )

    def create_log_for_recipient(self, type: InquiryLogMessage.MessageType) -> None:
        """Create log for recipient"""
        message = InquiryLogMessage.objects.get(message_type=type)
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
        # request_new(self) # deprecated since we're sending emails in different way

    @transition(field=status, source=[STATUS_SENT], target=STATUS_RECEIVED)
    def read(self):
        """Should be appeared when message readed/seen by recipient"""

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
        self.set_bodies()
        # request_accepted(self) # deprecated since we're sending emails in different way

    @transition(
        field=status,
        source=ACTIVE_STATES,
        target=STATUS_REJECTED,
    )
    def reject(self) -> None:
        """Should be appeared when message was rejected by recipient"""
        self.create_log_for_sender(InquiryLogMessage.MessageType.REJECTED)
        # request_declined(self) # deprecated since we're sending emails in different way

    def save(self, *args, **kwargs):
        adding = self._state.adding

        if self.status == self.STATUS_NEW:
            self.send()

        super().save(*args, **kwargs)

        if adding:
            self.sender.userinquiry.increment()  # type: ignore
            self.create_log_for_recipient(InquiryLogMessage.MessageType.NEW)

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
