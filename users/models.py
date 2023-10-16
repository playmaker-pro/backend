import datetime
from urllib.parse import urljoin

import uuid
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

from notifications.mail import (
    mail_user_waiting_for_verification,
    verification_notification,
)
from roles import definitions
from users.managers import CustomUserManager
from utils import calculate_age


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
    def is_parent(self):
        return self.role == definitions.PARENT_SHORT

    @property
    def is_guest(self):
        return self.role == definitions.GUEST_SHORT

    @property
    def profile(self):
        if self.is_player:
            return self.playerprofile
        elif self.is_coach:  # @todo unified access to this T P... and other types.
            return self.coachprofile
        elif self.is_club:
            return self.clubprofile
        elif self.is_manager:
            return self.managerprofile
        elif self.is_scout:
            return self.scoutprofile
        elif self.is_parent:
            return self.parentprofile
        elif self.is_guest:
            return self.guestprofile
        elif self.role is None:
            return self.guestprofile
        else:
            return None

    def get_admin_url(self):
        return reverse(
            f"admin:{self._meta.app_label}_{self._meta.model_name}_change",
            args=(self.id,),
        )


class User(AbstractUser, UserRoleMixin):
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

    STATES = list(zip(STATES, STATES))
    # Verfied means - user is who he declar

    state = FSMField(default=STATE_NEW, choices=STATES)

    first_name = models.CharField(
        _("first name"), max_length=150, blank=True, null=True
    )
    last_name = models.CharField(_("last name"), max_length=150, blank=True, null=True)

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

        :param: extra dict where additional information can be putted by entity changing state.
        example:
            extra['reason'] = 'User removed field1'
        """

    @transition(field=state, source="*", target=STATE_ACCOUNT_VERIFIED)
    def verify(self, silent: bool = False, extra: dict = None):
        """Account is verified by admins/site managers.

        :param: extra - dict where additional information can be putted by entity changing state.
        example:
            extra['reason'] = 'User removed field1'
        """
        if not silent:
            verification_notification(self)

    @transition(
        field=state, source="*", target=STATE_ACCOUNT_WAITING_FOR_VERIFICATION_DATA
    )
    def missing_verification_data(self, silent: bool = False, extra: dict = None):
        """In case when user remove or alter verification fields in his account transition to this state should occure.
        Which means that account has missing verification fields in profile.

        :param: extra - dict where additional information can be putted by entity changing state.
               example:
                    extra['reason'] = 'User removed field1'
        """

    @transition(field=state, source="*", target=STATE_ACCOUNT_WAITING_FOR_VERIFICATION)
    def waiting_for_verification(self, silent: bool = False, extra: dict = None):
        """Account is verified by admins/site managers.

        :param: extra  - dict where additional information can be putted by entity changing state.
        example:
            extra['reason'] = 'User removed field1'
        """
        if extra:
            reason = extra.get("reason")
        else:
            reason = None
        mail_user_waiting_for_verification(self, extra_body=reason)

    @transition(field=state, source="*", target=STATE_ACCOUNT_WAITING_FOR_VERIFICATION)
    def unverify(self, silent: bool = False, extra: dict = None):
        """Account is verified by admins/site managers.

        :param: extra  - dict where additional information can be putted by entity changing state.
        example:
            extra['reason'] = 'User removed field1'
        """

        if extra:
            reason = extra.get("reason")
        else:
            reason = None
        mail_user_waiting_for_verification(self, extra_body=reason)

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
        return self.declared_role

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
    last_activity = models.DateTimeField(
        _("Last Activity"), default=None, null=True, blank=True
    )

    # verification = models.OneToOneField(
    #     "VerificationStatus",
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True
    # )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_declared_role_display()})"

    def save(self, *args, **kwargs):
        if self.role in [
            definitions.GUEST_SHORT,
            definitions.SCOUT_SHORT,
            definitions.PARENT_SHORT,
            definitions.MANAGER_SHORT,
        ]:
            if self.state != self.STATE_ACCOUNT_VERIFIED:
                self.state = self.STATE_ACCOUNT_VERIFIED
        super().save(*args, **kwargs)

        # state_after = self.state
        # raise RuntimeError(state_after, state_before)
        # if state_before != self.STATE_ACCOUNT_VERIFIED and state_after == self.STATE_ACCOUNT_VERIFIED:
        #     pass
        # verification_notification(self)

    def new_user_activity(self):
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

    @property
    def age(self):
        return calculate_age(self.birth_date)

    class Meta:
        verbose_name = "User Preference"
        verbose_name_plural = "User Preferences"
