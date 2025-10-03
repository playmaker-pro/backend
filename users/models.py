import datetime
import uuid
from typing import List
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django_countries import countries
from django_fsm import FSMField, transition
from pydantic import typing

from roles import definitions
from users.managers import CustomUserManager
from utils import calculate_age, generate_fe_url_path


class UserRoleMixin:
    @property
    def is_player(self):
        return self.role == definitions.PLAYER_SHORT

    @property
    def is_coach(self):
        return self.role == definitions.COACH_SHORT

    @property
    def is_club(self):
        return self.role == definitions.CLUB_SHORT

    @property
    def is_manager(self):
        return self.role == definitions.MANAGER_SHORT

    @property
    def is_scout(self):
        return self.role == definitions.SCOUT_SHORT

    @property
    def is_guest(self):
        return self.role == definitions.GUEST_SHORT

    @property
    def profile(self):
        """Get profile based on declared role"""
        if role_name := definitions.PROFILE_TYPE_MAP.get(self.declared_role, None):
            return getattr(self, f"{role_name}profile", None)

    def get_admin_url(self):
        return reverse(
            f"admin:{self._meta.app_label}_{self._meta.model_name}_change",
            args=(self.id,),
        )


class User(AbstractUser, UserRoleMixin):
    class DisplayStatus(models.TextChoices):
        NOT_SHOWN = "Niewyświetlany"
        UNDER_REVIEW = "W trakcie analizy"
        VERIFIED = "Zweryfikowany"

    ROLE_CHOICES = definitions.ACCOUNT_ROLES

    STATE_NEW = "New"
    STATE_AUTH_VERIFIED = "Authentication Verified"
    STATE_ACCOUNT_WAITING_FOR_VERIFICATION_DATA = (
        "Awaiting for user's verification input"
    )
    STATE_ACCOUNT_WAITING_FOR_VERIFICATION = "Account Waiting For Verification"
    STATE_ACCOUNT_VERIFIED = "Account Verified"
    STATE_MIGRATED_VERIFIED = "Migrated Verified"
    STATE_MIGRATED_NEW = "Migrated New"

    STATES = (
        STATE_NEW,
        STATE_AUTH_VERIFIED,
        STATE_ACCOUNT_WAITING_FOR_VERIFICATION_DATA,
        STATE_ACCOUNT_WAITING_FOR_VERIFICATION,
        STATE_ACCOUNT_VERIFIED,
        STATE_MIGRATED_VERIFIED,
        STATE_MIGRATED_NEW,
    )
    username = None
    STATES = list(zip(STATES, STATES))
    # Verfied means - user is who he declar

    state = FSMField(default=STATE_NEW, choices=STATES)

    first_name = models.CharField(
        _("first name"), max_length=150, blank=True, null=True
    )
    last_name = models.CharField(_("last name"), max_length=150, blank=True, null=True)

    display_status = models.CharField(
        max_length=20,
        choices=DisplayStatus.choices,
        default=DisplayStatus.VERIFIED,
        help_text="Status for managing visibility in databases",
    )

    @transition(
        field=state,
        source=[
            STATE_NEW,
            STATE_MIGRATED_NEW,
            STATE_MIGRATED_VERIFIED,
            STATE_ACCOUNT_WAITING_FOR_VERIFICATION_DATA,
        ],
        target=STATE_AUTH_VERIFIED,
    )
    def verify_email(self, silent: bool = False, extra: dict = None):
        """Account's email has been verified by user

        :param: extra dict where additional information can be putted by entity
        changing state.
        example:
            extra['reason'] = 'User removed field1'
        """

    @transition(field=state, source="*", target=STATE_ACCOUNT_VERIFIED)
    def verify(self, silent: bool = False, extra: dict = None):
        """Account is verified by admins/site managers.

        :param: extra - dict where additional information can be putted by entity
        changing state.
        example:
            extra['reason'] = 'User removed field1'
        """
        # if not silent:
        #     verification_notification(self)

    @transition(
        field=state, source="*", target=STATE_ACCOUNT_WAITING_FOR_VERIFICATION_DATA
    )
    def missing_verification_data(self, silent: bool = False, extra: dict = None):
        """In case when user remove or alter verification fields in his account
        transition to this state should occure.
        Which means that account has missing verification fields in profile.

        :param: extra - dict where additional information can be putted by entity
        changing state.
               example:
                    extra['reason'] = 'User removed field1'
        """

    @transition(field=state, source="*", target=STATE_ACCOUNT_WAITING_FOR_VERIFICATION)
    def waiting_for_verification(self, silent: bool = False, extra: dict = None):
        """Account is verified by admins/site managers.

        :param: extra  - dict where additional information can be putted by entity
        changing state.
        example:
            extra['reason'] = 'User removed field1'
        """
        if extra:
            reason = extra.get("reason")
        else:
            reason = None
        # mail_user_waiting_for_verification(self, extra_body=reason)

    @transition(field=state, source="*", target=STATE_ACCOUNT_WAITING_FOR_VERIFICATION)
    def unverify(self, silent: bool = False, extra: dict = None):
        """Account is verified by admins/site managers.

        :param: extra  - dict where additional information can be putted by entity
        changing state.
        example:
            extra['reason'] = 'User removed field1'
        """

        if extra:
            reason = extra.get("reason")
        else:
            reason = None
        # mail_user_waiting_for_verification(self, extra_body=reason)

    @property
    def email_username(self):
        return self.email.split("@")[0]

    @property
    def display_name(self):
        return self.email_username

    @property
    def display_full_name(self):
        return " ".join(filter(None, [self.first_name, self.last_name]))

    @property
    def role(self):
        return self.declared_role or self.historical_role

    @property
    def is_missing_verification_data(self):
        return self.state == self.STATE_ACCOUNT_WAITING_FOR_VERIFICATION_DATA

    @property
    def is_migrated(self):
        return self.state in [self.STATE_MIGRATED_NEW, self.STATE_MIGRATED_VERIFIED]

    @property
    def is_auth_verified(self):
        return self.state == self.STATE_AUTH_VERIFIED

    @property
    def is_new_state(self):
        return self.state == self.STATE_NEW

    @property
    def is_waiting_for_verification(self):
        return self.state == self.STATE_ACCOUNT_WAITING_FOR_VERIFICATION

    @property
    def is_verified(self):
        return self.state == self.STATE_ACCOUNT_VERIFIED

    @property
    def is_need_verfication_role(self):
        return self.is_player or self.is_coach or self.is_club

    @property
    def is_pending_role_change(self):
        return self.changerolerequestor.filter(approved=False).count() > 0

    def validate_last_name(self):
        if len(self.last_name) < 2:
            return False
        return True

    def pending_role_change(self):
        return self.changerolerequestor.filter(approved=False).last()

    @property
    def is_roleless(self):
        return self.declared_role is None

    @classmethod
    def get_system_user(cls):
        return cls.objects.get(email=settings.SYSTEM_USER_EMAIL)

    def set_role(self, role: str) -> None:
        """set role and save, role need to be validated!"""
        self.declared_role = role
        self.save()

    @property
    def pm_score(self) -> typing.Optional[int]:
        """Get PlayMaker Score of given user (players only)"""
        try:
            return self.playerprofile.playermetrics.pm_score or None
        except models.ObjectDoesNotExist:
            return None

    finish_account_initial_setup = (
        models.BooleanField(  # @todo - remove this, it is deprecated.
            _("Skip full setup"),
            null=True,
            blank=True,
        )
    )

    email = models.EmailField(_("Adres email"), unique=True)

    # Note: As of now, this flag does not impact user access or functionalities.
    is_email_verified = models.BooleanField(
        default=False,
        help_text="Indicates whether the user's email address has been verified.",
    )

    def get_file_path(self, filename: str) -> str:
        """define user profile picture image path"""
        curr_date: str = str(datetime.datetime.now().date())
        format: str = filename.split(".")[-1]
        return f"profile_pics/{curr_date}/{str(uuid.uuid4())}.{format}"

    picture = models.ImageField(
        _("Zdjęcie"), upload_to=get_file_path, null=True, blank=True
    )

    declared_club = models.CharField(
        _("Deklaracja klubu"),
        max_length=355,
        null=True,
        blank=True,
        help_text="Users declaration in which club he plays.",
    )

    declared_role = models.CharField(
        _("Deklaracja roli"),
        choices=ROLE_CHOICES,
        max_length=355,
        null=True,
        blank=True,
        help_text="Users declaration in which role he has. It is main paramter.",
    )
    historical_role = models.CharField(
        _("Deklaracja historycznej roli"),
        choices=ROLE_CHOICES,
        max_length=355,
        null=True,
        blank=True,
        help_text="User role declaration from previous app version.",
    )
    last_activity = models.DateTimeField(
        _("Last Activity"), default=None, null=True, blank=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_declared_role_display()})"

    @property
    def should_be_listed(self) -> bool:
        """
        Determines if a user should be listed based on their name and display status.
        Users are listed if they have a proper name (not created from email) and their
        display status is either Verified or Under Review.
        """
        name_condition = (
            self.first_name and self.last_name and self.first_name != self.last_name
        )
        display_status_condition = self.display_status in [
            User.DisplayStatus.VERIFIED,
            User.DisplayStatus.UNDER_REVIEW,
        ]
        return name_condition and display_status_condition

    def save(self, *args, **kwargs):
        if self.role in [
            definitions.GUEST_SHORT,
            definitions.SCOUT_SHORT,
            definitions.MANAGER_SHORT,
        ]:
            if self.state != self.STATE_ACCOUNT_VERIFIED:
                self.state = self.STATE_ACCOUNT_VERIFIED
        super().save(*args, **kwargs)

    def update_activity(self):
        """
        Update the user's last activity timestamp.

        This method sets the user's `last_activity` attribute to the current time and
        then saves the change to the database.
        """
        self.last_activity = timezone.now()
        self.save(update_fields=["last_activity"])

    @property
    def picture_url(self) -> str:
        """Generate club picture url"""
        if self.picture:
            return urljoin(settings.BASE_URL, self.picture.url)

    @property
    def contact_email(self) -> str:
        """
        Returns user contact email.
        This is the main place, from which we take user contact email used for
        example in sending notifications.
        """
        return self.userpreferences.contact_email or self.email

    def can_send_email(self, mailing_type: str) -> bool:
        """
        Check if user can receive given mailing type based on his preferences.
        If no preferences are set, we assume that user can receive all types of mailings.
        """
        if self.mailing and self.mailing.preferences:
            return getattr(self.mailing.preferences, mailing_type, True)
        return True

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


class UserPreferences(models.Model):
    COUNTRIES = countries

    GENDER_CHOICES = (
        ("M", _("Mężczyzna")),
        ("K", _("Kobieta")),
    )
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    localization = models.ForeignKey(
        "cities_light.City",
        verbose_name=_("Localization"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="User's localization (city and voivodeship)",
    )
    citizenship = ArrayField(
        models.CharField(max_length=100, choices=COUNTRIES),
        blank=True,
        null=True,
        help_text="User's citizenship (country of citizenship)",
    )
    spoken_languages = models.ManyToManyField(
        "profiles.Language",
        blank=True,
        help_text="User's known languages (languages spoken by the user)",
    )
    gender = models.CharField(
        _("Gender"),
        choices=GENDER_CHOICES,
        max_length=1,
        blank=True,
        null=True,
        help_text="User's gender (represents the gender identity of the user)",
    )
    birth_date = models.DateField(
        _("Data urodzenia"), blank=True, null=True, help_text="User's date of birth"
    )
    phone_number = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        help_text="Phone number for the transfer.",
    )
    dial_code = models.IntegerField(
        _("Dial Code"),
        blank=True,
        null=True,
        help_text=_("Country dial code for the phone number."),
    )
    contact_email = models.EmailField(
        _("Contact Email"),
        blank=True,
        null=True,
        help_text=_("Contact email address for the transfer."),
    )

    @property
    def inquiry_contact(self) -> str:
        return f"+{self.dial_code}{self.phone_number}"

    @property
    def age(self):
        return calculate_age(self.birth_date)

    class Meta:
        verbose_name = "User Preference"
        verbose_name_plural = "User Preferences"


class Ref(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, primary_key=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    title = models.CharField(
        max_length=30, verbose_name="Krótki tytuł", null=True, blank=True
    )
    description = models.TextField(null=True, blank=True, verbose_name="Opis")

    def __str__(self) -> str:
        return f"[{self.uuid}] {self.user or self.title}"

    @property
    def registered_users(self) -> models.QuerySet:
        return self.referrals.all()

    @property
    def registered_users_premium(self) -> List:
        return [user for user in self.registered_users if user.bought_premium]

    @property
    def url(self) -> str:
        return generate_fe_url_path("?ref_code=" + str(self.uuid))

    @property
    def is_user(self) -> bool:
        return self.user is not None

    class Meta:
        verbose_name = "Afiliacja"
        verbose_name_plural = "Afiliacje"


class UserRef(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ref_by = models.ForeignKey(
        Ref,
        on_delete=models.CASCADE,
        related_name="referrals",
        verbose_name="Referred by",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ref_by} zaprosił {self.user}"

    @property
    def bought_premium(self) -> bool:
        return self.user.transaction_set.filter(
            product__ref="PREMIUM", transaction_status="SUCCESS"
        ).exists()

    class Meta:
        verbose_name = "Zaproszenie afiliacyjne"
        verbose_name_plural = "Zaproszenia afiliacyjne"
