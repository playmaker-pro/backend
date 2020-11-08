from django.db import models
from datetime import datetime
from django.contrib.auth.models import AbstractUser
# from users.models import MembershipStatus
from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import ugettext_lazy as _
from django_fsm import FSMField, transition
from notifications.mail import mail_user_waiting_for_verification


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, username=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)


BEFORE_FIRST_LOGIN = 'before_first_login'
FIRST_LOGIN = 'first_login'

PLAYER_SHORT, PLAYER_FULL = 'P', 'Piłkarz'
COACH_SHORT, COACH_FULL = 'T', 'Trener'
CLUB_SHORT, CLUB_FULL = 'C', 'Klub / Szkółka'
GUEST_SHORT, GUEST_FULL = 'G', 'Kibic / Rodzic'


ACCOUNT_ROLES = (
        ('P', 'Piłkarz'),
        ('T', 'Trener'),
        ('G', 'Gość'),
        ('C', 'Klub'),
)


class UserVerification(models.Model):  # @todo: to be removed - deprecated due to FSM state on User model
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='userforverification',
        help_text='User who shoudl be verified.')

    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='approver',
        help_text='Admin who verified.')

    approved = models.BooleanField(
        default=False,
        help_text='Defines if admin approved change')

    request_date = models.DateTimeField(auto_now_add=True)

    accepted_date = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.approved:
            self.accepted_date = datetime.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user}'s request to change profile from {self.current} to {self.new}"





class UserRoleMixin:
    @property
    def is_coach(self):
        return self.role == 'T'

    @property
    def is_player(self):
        return self.role == 'P'

    @property
    def is_club(self):
        return self.role == 'C'

    @property
    def is_scout(self):
        return self.role == 'SK'

    @property
    def is_manager(self):
        return self.role == 'M'

    @property
    def is_guest(self):
        return self.role == 'G'

    @property
    def is_standard(self):
        return self.role == 'S'


class User(AbstractUser, UserRoleMixin):

    ROLE_CHOICES = ACCOUNT_ROLES

    STATE_NEW = 'New'
    STATE_AUTH_VERIFIED = 'Authentication Verified'
    STATE_ACCOUNT_VERIFIED = 'Account Verified'
    STATE_MIGRATED = 'Migrated'
    STATE_ACTIVATED = 'Activated'
    STATE_LOCKED = 'Locked'
    STATE_BANNED = 'Banned'

    STATES = (
        STATE_NEW,
        STATE_AUTH_VERIFIED,
        STATE_ACCOUNT_VERIFIED,
        STATE_MIGRATED,
        STATE_ACTIVATED,
        STATE_LOCKED,
        STATE_BANNED
    )

    STATES = list(zip(STATES, STATES))
    # Verfied means - user is who he declar

    state = FSMField(default=STATE_NEW, choices=STATES)

    @transition(field=state,  source=[STATE_NEW, STATE_MIGRATED], target=STATE_AUTH_VERIFIED)
    def verify_email(self):
        """Account's email has been verified by user"""
        mail_user_waiting_for_verification(self)

    @transition(field=state, source=[STATE_AUTH_VERIFIED], target=STATE_ACCOUNT_VERIFIED)
    def verify(self):
        """Account is verified by admins/site managers."""

    @transition(field=state, source=[STATE_ACCOUNT_VERIFIED], target=STATE_AUTH_VERIFIED)
    def unverify(self):
        """Account is verified by admins/site managers."""

    @transition(field=state, source=[STATE_ACCOUNT_VERIFIED], target=STATE_ACTIVATED)
    def active(self):
        """Fully unlocked account"""

    @transition(field=state, source=[STATE_ACCOUNT_VERIFIED, STATE_ACTIVATED], target=STATE_LOCKED)
    def lock(self):
        """Account locked"""

    @transition(field=state, source='*', target=STATE_BANNED)
    def ban(self):
        """Banned account"""

    @property
    def is_new_state(self):
        return self.state == self.STATE_NEW

    @property
    def is_verified(self):
        return self.state == self.STATE_ACCOUNT_VERIFIED

    @property
    def is_pending_role_change(self):
        return self.changerolerequestor.filter(approved=False).count() > 0

    def pending_role_change(self):
        return self.changerolerequestor.filter(approved=False).last()

    finish_account_initial_setup = models.BooleanField(
        _('Skip full setup'),
        null=True,
        blank=True,
    )

    email = models.EmailField(_('email address'), unique=True)

    picture = models.ImageField(
        _("Profile picture"),
        upload_to="profile_pics/%Y-%m-%d/",
        null=True,
        blank=True)

    @property
    def role(self):
        return self.declared_role

    @property
    def profile(self):
        if self.is_coach:  # @todo unified access to this T P... and other types.
            return self.coachprofile

        elif self.is_player:
            return self.playerprofile

        elif self.is_club:
            return self.clubprofile

        elif self.is_guest:
            return self.guestprofile

        elif self.role is None or self.is_standard:
            return self.standardprofile
        else:
            return None

    declared_club = models.CharField(
        _('declared club'),
        max_length=355,
        null=True,
        blank=True,
        help_text="Users declaration in which club he plays.")

    declared_role = models.CharField(
        _('declared role'),
        choices=ROLE_CHOICES,
        max_length=355,
        null=True,
        blank=True,
        help_text="Users declaration in which role he has. It is main paramter.")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    @property
    def email_username(self):
        return self.email.split('@')[0]

    @property
    def display_name(self):
        return self.email_username

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
