from django.db import models

from django.contrib.auth.models import AbstractUser
# from users.models import MembershipStatus


from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import ugettext_lazy as _
from django_fsm import FSMField, transition


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

ACCOUNT_ROLES = (
        ('P', 'Piłkarz'),
        ('T', 'Trener')
)
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class User(AbstractUser):
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    # ACCOUNT_STATE = {
    #    BEFORE_FIRST_LOGIN: BEFORE_FIRST_LOGIN,
    #   FIRST_LOGIN: FIRST_LOGIN,

    # }

    # @transition
    # def firstly_logged(self):
    #    pass

    ROLE_CHOICES = ACCOUNT_ROLES
    # account_state = FSMField(default='new')
    initial_setup = models.BooleanField(_('Skip full setup'), default=None, null=True, help_text="Flag ")

    email = models.EmailField(_('email address'), unique=True)

    # country = models.CharField(verbose_name='country', max_length=255, null=True, blank=True, default='A')  # @todo remove or replace with more miningfull data
    # status = models.ForeignKey(MembershipStatus, on_delete=models.SET_NULL, null=True, default=1)

    # content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    # object_id = models.PositiveIntegerField()
    # content_object = GenericForeignKey('content_type', 'object_id')   

    @property
    def profile(self):
        if self.declared_role == 'T':  # @todo unified access to this T P and other types.
            return self.coachprofile

        elif self.declared_role == 'P':
            return self.playerprofile

        else:
            return None

    declared_club = models.CharField(
        _('declared club'),
        max_length=355,
        null=True,
        blank=True,
        help_text="Users declaration in which club he plays.")

    declared_role = models.CharField(
        _('declared club'),
        choices=ROLE_CHOICES,
        max_length=355,
        null=True,
        blank=True,
        help_text="Users declaration in which role he has")

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
