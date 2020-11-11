
from datetime import datetime
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import ACCOUNT_ROLES
from django.core.validators import MinValueValidator, MaxValueValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.urls import reverse
from .utils import unique_slugify
from collections import Counter
from django_countries.fields import CountryField

PROFILE_TYPE_TO_DATA_MODELS = {
    'player': 'Player',
    'coach': 'Coach',
    'team': 'Teamn',
    'club': 'Club',
}


from django.contrib.auth import get_user_model


User = get_user_model()


class RoleChangeRequest(models.Model):
    """Keeps track on requested changes made by users."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='changerolerequestor',
        help_text='User who requested change')

    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        help_text='Admin who verified.')

    approved = models.BooleanField(
        default=False,
        help_text='Defines if admin approved change')

    request_date = models.DateTimeField(auto_now_add=True)

    accepted_date = models.DateTimeField(auto_now=True)

    new = models.CharField(max_length=100, choices=ACCOUNT_ROLES)

    class Meta:
        unique_together = ('user', 'request_date')

    @property
    def current(self):
        return self.user.get_declared_role_display()

    @property
    def current_pretty(self):
        return self.user.get_declared_role_display()

    @property
    def new_pretty(self):
        return self.get_new_display()

    def __str__(self):
        return f"{self.user}'s request to change profile from {self.current} to {self.new}"

    def save(self, *args, **kwargs):
        if self.approved:
            self.accepted_date = datetime.now()
        super().save(*args, **kwargs)

    def get_admin_url(self):
        return reverse(f"admin:{self._meta.app_label}_{self._meta.model_name}_change", args=(self.id,))


class BaseProfile(models.Model):
    """Base profile model to held most common profile elements"""
    PROFILE_TYPE = None

    COMPLETE_FIELDS = []  # this is definition of profile fields which will be threaded as mandatory for full profile.

    VERIFICATION_FIELDS = []  # this is definition of profile fields which will be threaded as must-have params.

    DATA_ITEM_MODEL = PROFILE_TYPE_TO_DATA_MODELS.get(PROFILE_TYPE)  # Player or League

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True)

    data_mapper_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=f'ID of object placed in data_ database. It should alwayes reflect scheme which represents.')

    slug = models.CharField(
        max_length=255,
        blank=True,
        editable=False)

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

    @property
    def is_complete(self):
        for field_name in self.COMPLETE_FIELDS:
            if getattr(self, field_name) is None:
                return False
        return True

    @property
    def is_not_complete(self):
        return not self.is_complete

    @property
    def percentage_completion(self):

        total = len(self.COMPLETE_FIELDS)

        if total == 0:
            return int(100)
        field_values = [getattr(self, field_name) for field_name in self.COMPLETE_FIELDS]
        part = total - Counter(field_values).get(None, 0)

        completion_percentage = 100 * float(part)/float(total)

        return int(completion_percentage)

    def __str__(self):
        return f"{self.user}'s {self.PROFILE_TYPE} profile"

    def save(self, *args, **kwargs):
        slug_str = "%s %s %s" % (self.PROFILE_TYPE, self.user.first_name, self.user.last_name)
        unique_slugify(self, slug_str)

        # check if fields has changed
        try:
            old_object = type(self).objects.get(pk=self.pk) if self.pk else None
            fresh_object = False
        except type(self).DoesNotExist:
            # it means first creation of object.
            fresh_object = True

        if not fresh_object:
            ver_old = []
            if old_object:
                ver_old = self._get_verification_field_values(old_object)
        
        # Queen of the show
        super().save(*args, **kwargs)

        # we are updating existing model (not first occurence)
        ver_new = self._get_verification_field_values(self)
        if not fresh_object:
            if self._verification_fileds_changed(ver_old, ver_new) and (self.user.is_verified or self.user.is_waiting_for_verification):
                self.user.unverify(extra={'reason': f'[verification-params-changed] params:{self.VERIFICATION_FIELDS})  Old:{ver_old} -> New:{ver_new}'})
                self.user.save()
        else:
            ver_old = ver_new
        # If User is not yet verified and have all needed params set for verification.
        # if those params didint changed during wairing for veritication
        if self.is_ready_for_verification() and self._verification_fileds_changed(ver_old, ver_new):
            self.user.unverify(extra={'reason': f'[verification-params-ready] params:{self.VERIFICATION_FIELDS})  values:{self._get_verification_field_values(self)}'})
            self.user.save()

    def is_ready_for_verification(self):
        return not self.user.is_verified and self._is_verification_fields_filled()

    def _is_verification_fields_filled(self):
        return all(self._get_verification_field_values(self))

    def _verification_fileds_changed(self, old, new):
        return old != new

    def _get_verification_field_values(self, obj):
        return [getattr(obj, field) for field in self.VERIFICATION_FIELDS]

    class Meta:
        abstract = True
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"


class PlayerProfile(BaseProfile):
    '''Player specific profile'''
    PROFILE_TYPE = 'player'

    VERIFICATION_FIELDS = [
        'birth_date',
        'country',
        'club_raw',
    ]

    COMPLETE_FIELDS = [
        'height',
        'weight',
        'formation',
        'prefered_leg',
        'card',
        'transfer_status',
        'phone',
    ]

    GOALKEEER = 'GK'
    DEFENDER_LEFT = 'DL'
    POSITION_CHOICES = [
        (GOALKEEER, 'Bramkarz'),
        (DEFENDER_LEFT, 'Obrońca Lewy'),
    ]

    LEG_CHOICES = (
        ('Lewa', 'Lewa'),
        ('Prawa', 'Prawa')
    )
    TRANSFER_STATUS_CHOICES = (
        ('SC', 'Szukam klubu'),
        ('RO', 'Rozważę wszelkie oferty'),
        ('NC', 'Nie szukam klubu')
    )
    CARD_CHOICES = (
        ('MKN', 'Mam kartę na ręku'),
        ('NCMKN', 'Nie wiem czy mam kartę na ręku'),
        ('NKN', 'Nie mam karty na ręku')
    )
    FORMATION_CHOICES = (
        ('5-3-2', '5-3-2'),
        ('5-4-1', '5-4-1'),
        ('4-4-2', '4-4-2'),
        ('4-5-1', '4-5-1'),
        ('4-3-3', '4-3-3'),
        ('4-2-3-1', '4-2-3-1'),
        ('4-1-4-1', '4-1-4-1'),
        ('4-3-2-1', '4-3-2-1'),
        ('3-5-2', '3-5-2'),
        ('3-4-3', '3-4-3')
    )

    GOAL_CHOICES = (
        (0, 'Ekstraklasa'),
        (1, '1 liga'),
        (2, '2 liga'),
        (3, '3 liga'),
        (4, '4 liga'),
        (5, '5 liga'),
        (6, 'A klasa'),
        (7, 'B klasa')
    )
    birth_date = models.DateField(
        _('Birth date'),
        blank=True,
        null=True)

    height = models.PositiveIntegerField(
        _('Height'),
        blank=True,
        null=True,
        help_text='Height (cm)',
        validators=[MinValueValidator(130), MaxValueValidator(210)])

    weight = models.PositiveIntegerField(
        _('Weight'),
        blank=True,
        null=True,
        help_text='Weight (kg)',
        validators=[MinValueValidator(40), MaxValueValidator(140)])

    country = CountryField(
        _('Country'),
        blank=True,
        null=True,
        blank_label='(select country)'
    )

    club_raw = models.CharField(
        _('Club name'),
        max_length=68,
        blank=True,
        null=True)

    team_raw = models.CharField(
        _('Team name'), max_length=68, blank=True, null=True)
    league_raw = models.CharField(
        _('League name'), max_length=68, blank=True, null=True)
    voivodeship_raw = models.CharField(
        _('Voivodeship name'), max_length=68, blank=True, null=True)

    position_raw = models.CharField(_('Position name'), max_length=30, choices=POSITION_CHOICES, blank=True, null=True)
    formation = models.CharField(_('Formation'), choices=FORMATION_CHOICES, max_length=11, null=True, blank=True)
    alt_formation = models.CharField(_('Formation'), choices=FORMATION_CHOICES, max_length=11, null=True, blank=True)
    prefered_leg = models.CharField(_('prefered leg'), choices=LEG_CHOICES, max_length=30, null=True, blank=True)

    transfer_status = models.CharField(_('transfer status'), choices=TRANSFER_STATUS_CHOICES, max_length=45, null=True, blank=True)
    # about_me = models.TextField(_('about me'), blank=True)
    card = models.CharField(_('karta na ręku'), choices=CARD_CHOICES, max_length=60, null=True, blank=True)

    soccer_goal = models.CharField(_('karta na ręku'), choices=GOAL_CHOICES, max_length=60, null=True, blank=True)

    phone = PhoneNumberField(blank=True, null=True)
    facebook_url = models.URLField(blank=True, null=True)
    lnp_url = models.URLField(blank=True, null=True)
    min90_url = models.URLField(blank=True, null=True)
    transfermarket_url = models.URLField(blank=True, null=True)

    practice_distance = models.PositiveIntegerField(
        _('max practice distance'),
        blank=True,
        null=True,
        help_text='max practice distance',
        validators=[MinValueValidator(10), MaxValueValidator(500)])

    @property
    def age(self):  # @todo it is taken from external source need to chcek this.... 
        if not self.birth_date:
            return False
        else:
            import datetime
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
    PROFILE_TYPE = 'club'

    phone = PhoneNumberField(blank=True, null=True)

    class Meta:
        verbose_name = "Club Profile"
        verbose_name_plural = "Club Profiles"


class CoachProfile(BaseProfile):
    PROFILE_TYPE = 'coach'
    COMPLETE_FIELDS = ['birth_date', 'phone']
    VERIFICATION_FIELDS = ['birth_date']

    GOALS_CHOICES = (
        ('Profesjonalna kariera', 'Profesjonalna kariera'),
        ('Kariera regionalna', 'Kariera regionalna'),
        ('Trenerka jako hobby', 'Trenerka jako hobby'),
    )

    phone = PhoneNumberField(blank=True, null=True)
    facebook_url = models.URLField(blank=True, null=True)
    soccer_goal = models.CharField(_('soccer goal'), choices=GOALS_CHOICES, max_length=60, null=True, blank=True)
    birth_date = models.DateField(
        _('birth date'),
        blank=True,
        null=True)

    class Meta:
        verbose_name = "Coach Profile"
        verbose_name_plural = "Coaches Profiles"


class StandardProfile(BaseProfile):  # @todo to be removed
    '''Regular base profile'''
    PROFILE_TYPE = 'standard'

    class Meta:
        verbose_name = "Standard Profile"
        verbose_name_plural = "Standard Profiles"


class GuestProfile(BaseProfile):   # @todo to be removed
    PROFILE_TYPE = 'guest'

    class Meta:
        verbose_name = "Guest Profile"
        verbose_name_plural = "Guests Profiles"


class ManagerProfile(BaseProfile):
    PROFILE_TYPE = 'manager'

    class Meta:
        verbose_name = "Manager Profile"
        verbose_name_plural = "Managers Profiles"


class FanProfile(BaseProfile):
    PROFILE_TYPE = 'fan'

    class Meta:
        verbose_name = "Fan Profile"
        verbose_name_plural = "Fans Profiles"


class ParentProfile(BaseProfile):
    PROFILE_TYPE = 'parent'

    class Meta:
        verbose_name = "Parent Profile"
        verbose_name_plural = "Parents Profiles"


class ScoutProfile(BaseProfile):
    PROFILE_TYPE = 'scout'

    class Meta:
        verbose_name = "Scout Profile"
        verbose_name_plural = "Scouts Profiles"
