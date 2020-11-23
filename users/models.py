from django.db import models
from datetime import datetime
from django.contrib.auth.models import AbstractUser
# from users.models import MembershipStatus
from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import ugettext_lazy as _
from django_fsm import FSMField, transition
from notifications.mail import mail_user_waiting_for_verification
from django.urls import reverse


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


PLAYER_SHORT, PLAYER_FULL = 'P', 'Piłkarz'
COACH_SHORT, COACH_FULL = 'T', 'Trener'
CLUB_SHORT, CLUB_FULL = 'C', 'Klub / Szkółka'
GUEST_SHORT, GUEST_FULL = 'G', 'Kibic / Rodzic'


ACCOUNT_ROLES = (
        ('P', 'Piłkarz'),
        ('T', 'Trener'),
        ('G', 'Gość'),  # deprecated
        ('C', 'Klub / Szkółka'),
        ('SK', 'Scout'),
        ('R', 'Rodzic'),
        ('K', 'Kibic'),
        ('M', 'Manadżer'),
        ('S', 'Standardowe'),
)


class UserRoleMixin:
    @property
    def is_player(self):
        return self.role == 'P'

    @property
    def is_coach(self):
        return self.role == 'T'

    @property
    def is_guest(self):
        return self.role == 'G'

    @property
    def is_club(self):
        return self.role == 'C'

    @property
    def is_scout(self):
        return self.role == 'SK'

    @property
    def is_parent(self):
        return self.role == 'R'

    @property
    def is_fan(self):
        return self.role == 'K'

    @property
    def is_manager(self):
        return self.role == 'M'

    @property
    def is_standard(self):
        return self.role == 'S'

    @property
    def profile(self):
        if self.is_player:
            return self.playerprofile
        elif self.is_coach:  # @todo unified access to this T P... and other types.
            return self.coachprofile
        elif self.is_guest:
            return self.guestprofile
        elif self.is_club:
            return self.clubprofile
        elif self.is_scout:
            return self.scoutprofile
        elif self.is_parent:
            return self.parentprofile
        elif self.is_fan:
            return self.fanprofile
        elif self.is_manager:
            return self.managerprofile

        elif self.role is None or self.is_standard:
            return self.standardprofile
        else:
            return None

    def get_admin_url(self):
        return reverse(f"admin:{self._meta.app_label}_{self._meta.model_name}_change", args=(self.id,))


class User(AbstractUser, UserRoleMixin):

    ROLE_CHOICES = ACCOUNT_ROLES

    STATE_NEW = 'New'
    STATE_AUTH_VERIFIED = 'Authentication Verified'
    STATE_ACCOUNT_WAITING_FOR_VERIFICATION_DATA = 'Awaiting for user\'s verification input'
    STATE_ACCOUNT_WAITING_FOR_VERIFICATION = "Account Waiting For Verification"
    STATE_ACCOUNT_VERIFIED = 'Account Verified'
    STATE_MIGRATED_VERIFIED = 'Migrated Verified'
    STATE_MIGRATED_NEW = 'Migrated New'

    STATES = (
        STATE_NEW,
        STATE_AUTH_VERIFIED,
        STATE_ACCOUNT_WAITING_FOR_VERIFICATION_DATA,
        STATE_ACCOUNT_WAITING_FOR_VERIFICATION,
        STATE_ACCOUNT_VERIFIED,
        STATE_MIGRATED_VERIFIED,
        STATE_MIGRATED_NEW,
        # STATE_ACTIVATED,
        # STATE_LOCKED,
        # STATE_BANNED
    )

    STATES = list(zip(STATES, STATES))
    # Verfied means - user is who he declar

    state = FSMField(default=STATE_NEW, choices=STATES)

    @transition(field=state,  source=[STATE_NEW, STATE_MIGRATED_NEW, STATE_MIGRATED_VERIFIED, STATE_ACCOUNT_WAITING_FOR_VERIFICATION_DATA], target=STATE_AUTH_VERIFIED)
    def verify_email(self, extra: dict = None):
        '''Account's email has been verified by user

        :param: extra dict where additional information can be putted by entity changing state.
        example:
            extra['reason'] = 'User removed field1'
        '''

    @transition(field=state, source=[STATE_AUTH_VERIFIED, STATE_MIGRATED_VERIFIED], target=STATE_ACCOUNT_VERIFIED)
    def verify(self, extra: dict = None):
        '''Account is verified by admins/site managers.

        :param: extra - dict where additional information can be putted by entity changing state.
        example:
            extra['reason'] = 'User removed field1'
        '''

    @transition(field=state, source='*', target=STATE_ACCOUNT_WAITING_FOR_VERIFICATION_DATA)
    def missing_verification_data(self, extra: dict = None):
        '''In case when user remove or alter verification fields in his account transition to this state should occure.
        Which means that account has missing verification fields in profile.

        :param: extra - dict where additional information can be putted by entity changing state.
               example:
                    extra['reason'] = 'User removed field1'
        '''

    @transition(field=state, source='*', target=STATE_ACCOUNT_WAITING_FOR_VERIFICATION)
    def waiting_for_verification(self, extra: dict = None):
        '''Account is verified by admins/site managers.

        :param: extra  - dict where additional information can be putted by entity changing state.
        example:
            extra['reason'] = 'User removed field1'
        '''
        if extra:
            reason = extra.get('reason')
        else:
            reason = None
        mail_user_waiting_for_verification(self, extra_body=reason)

    @transition(field=state, source='*', target=STATE_ACCOUNT_WAITING_FOR_VERIFICATION)
    def unverify(self, extra: dict = None):
        '''Account is verified by admins/site managers.

        :param: extra  - dict where additional information can be putted by entity changing state.
        example:
            extra['reason'] = 'User removed field1'
        '''
        if extra:
            reason = extra.get('reason')
        else:
            reason = None
        mail_user_waiting_for_verification(self, extra_body=reason)

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
    def is_pending_role_change(self):
        return self.changerolerequestor.filter(approved=False).count() > 0

    def pending_role_change(self):
        return self.changerolerequestor.filter(approved=False).last()

    @property
    def is_roleless(self):
        return self.declared_role is None

    finish_account_initial_setup = models.BooleanField(  # @todo - remove this, it is deprecated.
        _('Skip full setup'),
        null=True,
        blank=True,
    )

    email = models.EmailField(
        _('Adres email'), 
        unique=True)

    picture = models.ImageField(
        _("Zdjęcie"),
        upload_to="profile_pics/%Y-%m-%d/",
        null=True,
        blank=True)

    @property
    def role(self):
        return self.declared_role

    declared_club = models.CharField(
        _('Deklaracja klubu'),
        max_length=355,
        null=True,
        blank=True,
        help_text="Users declaration in which club he plays.")

    declared_role = models.CharField(
        _('Deklaracja roli'),
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
