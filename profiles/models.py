import datetime
import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


# @todo clean up with PEP8
class RoleChangeRequest(models.Model):
    """Keeps track on requested changes made by users."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True, related_name='requestor',
        help_text='User who requested change')

    approved = models.BooleanField(
        default=False,
        help_text='Defines if admin approved change')

    request_date = models.DateTimeField(auto_now_add=True)
    accepted_date = models.DateTimeField(auto_now=True)
    current = models.CharField(max_length=100)
    new = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user}'s request to change profile from {self.current} to {self.new}"


class BaseProfile(models.Model):
    """Base profile model"""
    profile_type = None

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True)

    slug = models.UUIDField(
        default=uuid.uuid4,
        blank=True,
        editable=False)

    picture = models.ImageField(
        _("Profile picture"),
        upload_to="profile_pics/%Y-%m-%d/",
        null=True, 
        blank=True)

    bio = models.CharField(
        _("Short Bio"),
        max_length=200,
        blank=True,
        null=True)

    email_verified = models.BooleanField(
        _("Email verified"),
        default=False,
        help_text="When user recieve confiramion and confirm it.")

    account_verified = models.BooleanField(
        _("Account verified"),
        default=False,
        help_text="Manually confirmed by Admin. This means that user is participant of soocer community.")

    def __str__(self):
        return f"{self.user}'s {self.profile_type} profile"

    class Meta:
        abstract = True
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"


class StandardProfile(BaseProfile):
    '''Regular base profile'''
    profile_type = 'standard'


class PlayerProfile(BaseProfile):
    '''Player specific profile'''

    profile_type = 'player'

    GOALKEEER = 'GK'
    DEFENDER_LEFT = 'DL'
    POSITION_CHOICES = [
        (GOALKEEER, 'Bramkarz'),
        (DEFENDER_LEFT, 'Obrońca Lewy'),
    ]

    birth_date = models.DateField(_('birth date'), blank=True, null=True)
    height = models.PositiveIntegerField(_('Height'), blank=True, null=True, help_text='Height (cm)')
    weight = models.PositiveIntegerField(_('Weight'), blank=True, null=True, help_text='Weight (kg)')
    club_raw = models.CharField(_('Club name'), max_length=68, blank=True, null=True)
    league_raw = models.CharField(_('League name'), max_length=68, blank=True, null=True)
    voivodeship_raw = models.CharField(_('Voivodeship name'), max_length=68, blank=True, null=True)
    position_raw = models.CharField(_('Position name'), max_length=30, choices=POSITION_CHOICES, blank=True, null=True)
    # about_me = models.TextField(_('about me'), blank=True)

    @property
    def age(self):  # @todo it is taken from external source need to chcek this.... 
        if not self.birth_date:
            return False
        else:
            today = datetime.date.today()
            # Raised when birth date is February 29 and the current year is not a
            # leap year.
            try:
                birthday = self.birth_date.replace(year=today.year)
            except ValueError:
                day = today.day - 1 if today.day != 1 else today.day + 2
                birthday = self.birth_date.replace(year=today.year, day=day)
            if birthday > today: return today.year - self.birth_date.year - 1
            else:
                return today.year - self.birth_date.year

    class Meta:
        verbose_name = "Player Profile"
        verbose_name_plural = "Player Profiles"


class ClubProfile(BaseProfile):
    profile_type = 'club'

    class Meta:
        verbose_name = "Coach Profile"
        verbose_name_plural = "Coach Profiles"


class CoachProfile(BaseProfile):
    profile_type = 'coach'

    class Meta:
        verbose_name = "Coach Profile"
        verbose_name_plural = "Coach Profiles"


class GuestProfile(BaseProfile):
    profile_type = 'guest'

    class Meta:
        verbose_name = "Guest Profile"
        verbose_name_plural = "Guest Profiles"
