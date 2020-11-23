
from collections import Counter
from datetime import datetime

from address.models import AddressField
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
from users.models import ACCOUNT_ROLES
from django.utils import timezone
from django.urls import reverse
from .utils import unique_slugify
from stats.adapters import PlayerAdapter
import utils as utilites


PROFILE_TYPE_TO_DATA_MODELS = {
    'player': 'Player',
    'coach': 'Coach',
    'team': 'Team',
    'club': 'Club',
}


class VerificationCompletionFieldsWrongSetup(Exception):
    pass


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


class ProfileVisitHistory(models.Model):

    counter = models.PositiveIntegerField(default=0)

    def increment(self):
        self.counter += 1
        self.save()


class BaseProfile(models.Model):
    """Base profile model to held most common profile elements"""
    PROFILE_TYPE = None

    VERIFICATION_FIELDS = []  # this is definition of profile fields which will be threaded as must-have params.

    COMPLETE_FIELDS = VERIFICATION_FIELDS + []  # this is definition of profile fields which will be threaded as mandatory for full profile.

    OPTIONAL_FIELDS = []

    DATA_ITEM_MODEL = PROFILE_TYPE_TO_DATA_MODELS.get(PROFILE_TYPE)  # Player or League

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True)

    history = models.OneToOneField(
        ProfileVisitHistory,
        on_delete=models.CASCADE,
        null=True,
        blank=True)

    data_mapper_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='ID of object placed in data_ database. It should alwayes reflect scheme which represents.')

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

    def get_permalink(self):
        return reverse("profiles:show", kwargs={"slug": self.slug})


    @property
    def is_complete(self):
        for field_name in self.COMPLETE_FIELDS + self.VERIFICATION_FIELDS:
            if getattr(self, field_name) is None:
                return False
        return True

    @property
    def has_data_id(self):
        return self.data_mapper_id is not None

    @property
    def is_not_complete(self):
        return not self.is_complete

    @property
    def percentage_completion(self):

        total = len(self.COMPLETE_FIELDS + self.VERIFICATION_FIELDS)

        if total == 0:
            return int(100)
        field_values = [getattr(self, field_name) for field_name in self.COMPLETE_FIELDS + self.VERIFICATION_FIELDS]

        part = total - Counter(field_values).get(None, 0)

        completion_percentage = 100 * float(part)/float(total)

        return int(completion_percentage)

    @property
    def percentage_left_verified(self):
        total = len(self.COMPLETE_FIELDS + self.VERIFICATION_FIELDS)
        total_fields_to_verify = len(self.VERIFICATION_FIELDS)
        if total_fields_to_verify == 0:
            return int(0)
        field_values = [getattr(self, field_name) for field_name in self.VERIFICATION_FIELDS]
        to_verify_count = len(list(filter(None, field_values)))

        left_fields_counter = total_fields_to_verify - to_verify_count
        try:
            left_verify_percentage = 100 * float(left_fields_counter)/float(total)
        except ZeroDivisionError:
            raise VerificationCompletionFieldsWrongSetup('Wrongly setuped COMPLETE_FIELDS and VERIFICATION_FIELDS')
        # print('a', field_values, to_verify_count, left_verify_percentage)
        return int(left_verify_percentage)

    def _get_verification_object_verification_fields(self):
        object_exists = False
        try:
            obj = type(self).objects.get(pk=self.pk) if self.pk else None
            if obj:
                fields_values = self._get_verification_field_values(obj)
                object_exists = True
            else:
                fields_values = None
        except type(self).DoesNotExist:
            # it means first creation of object.
            fields_values = None
        return fields_values, object_exists

    def _save_make_profile_history(self):
        if self.history is None:
            self.history = ProfileVisitHistory.objects.create()

    def save(self, *args, **kwargs):
        self._save_make_profile_history()

        slug_str = "%s %s %s" % (self.PROFILE_TYPE, self.user.first_name, self.user.last_name)
        unique_slugify(self, slug_str)

        ver_old, object_exists = self._get_verification_object_verification_fields()

        # Queen of the show
        super().save(*args, **kwargs)

        # we are updating existing model (not first occurence)
        ver_new = self._get_verification_field_values(self)
        if not object_exists:
            ver_old = ver_new

        # Cases when one of verification fields is None
        if self._is_verification_fields_filled():
            if not self.user.is_waiting_for_verification or not self.user.is_verified:
                self.user.waiting_for_verification(
                    extra={'reason': f'[verification-params-ready] params:{self.VERIFICATION_FIELDS})  Old:{ver_old} -> New:{ver_new}'})
                self.user.save()
            else:
                if self._verification_fileds_has_changed_and_was_filled(ver_old, ver_new):
                    self.user.unverify(extra={'reason': f'[verification-params-changed] params:{self.VERIFICATION_FIELDS})  Old:{ver_old} -> New:{ver_new}'})
                    self.user.save()
        else:
            if not self.user.is_missing_verification_data:
                self.user.missing_verification_data()  # -> change state to missing ver data
                self.user.save()

    def _is_verification_fields_filled(self):
        return all(self._get_verification_field_values(self))

    def _verification_fileds_has_changed_and_was_filled(self, old, new):
        return old != new and all(old) and all(new)

    def _get_verification_field_values(self, obj):
        return [getattr(obj, field) for field in self.VERIFICATION_FIELDS]

    def __str__(self):
        return f"{self.user}'s {self.PROFILE_TYPE} profile"

    class Meta:
        abstract = True
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"


def make_choices(choices):
    """
    Returns tuples of localized choices based on the dict choices parameter.
    Uses lazy translation for choices names.
    """
    return tuple([(k, _(v)) for k, v in choices])


class TrainerContact(models.Model):
    # @todo to be connected
    first_name = models.CharField(_('Imię'), max_length=255)
    last_name = models.CharField(_('Nazwisko'), max_length=255)
    season = models.CharField(_('Sezon'), max_length=255, null=True, blank=True)
    email = models.CharField(_('adres e-mail'), max_length=255, null=True, blank=True)
    phone = PhoneNumberField(_('Telefon'), blank=True, null=True)


class PlayerProfile(BaseProfile):
    '''Player specific profile'''
    PROFILE_TYPE = 'player'

    VERIFICATION_FIELDS = [
        'country',
        'birth_date',
        'team_club_league_voivodeship_ver',
    ]

    COMPLETE_FIELDS = [
       'height',
       'weight',
       'formation',
       'prefered_leg',
       'transfer_status',
       'card',
       'soccer_goal',
       'phone',
       'address',
       'practice_distance',
       'about',
       'training_ready',
       'league',
       # 'league_raw',
       # 'club_raw',
       # 'club',  # @todo this is kicked-off waiting for club mapping implementation
       'team',
       # 'team_raw',
       'position_raw',
       'voivodeship',
       # 'voivodeship_raw',
    ]

    OPTIONAL_FIELDS = [
        'position_raw_alt',
        'formation_alt',
        'facebook_url',
        'laczynaspilka_url',
        'min90_url',
        'transfermarket_url',
        'agent_status',
        'agent_name',
        'agent_phone',
        'agent_name',
    ]

    POSITION_CHOICES = [
        (1, 'Bramkarz'),
        (2, 'Obrońca Lewy'),
        (3, 'Obrońca Prawy'),
        (4, 'Obrońca Środkowy'),
        (5, 'Pomocnik defensywny (6)'),
        (6, 'Pomocnik środkowy (8)'),
        (7, 'Pomocnik ofensywny (10)'),
        (8, 'Skrzydłowy'),
        (9, 'Napastnik'),
    ]

    FANTASY_GOAL_KEEPER = 'bramkarz'
    FANTASY_DEFENDER = 'obronca'
    FANTASY_HELPER = 'pomocnik'
    FANTASY_ATTAKER = 'napastnik'

    FANTASY_MAPPING = {
            1: FANTASY_GOAL_KEEPER,
            2: FANTASY_DEFENDER,
            3: FANTASY_DEFENDER,
            4: FANTASY_DEFENDER,
            5: FANTASY_HELPER,
            6: FANTASY_HELPER,
            7: FANTASY_HELPER,
            8: FANTASY_HELPER,
            9: FANTASY_ATTAKER,
    }

    LEG_CHOICES = (
        (1, 'Lewa'),
        (2, 'Prawa')
    )

    TRANSFER_STATUS_CHOICES = (
        (1, 'Szukam klubu'),
        (2, 'Rozważę wszelkie oferty'),
        (3, 'Nie szukam klubu')
    )

    CARD_CHOICES = (
        (1, 'Mam kartę na ręku'),
        (2, 'Nie wiem czy mam kartę na ręku'),
        (3, 'Nie mam karty na ręku')
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

    AGENT_STATUS_CHOICES = (
        (1, 'Mam agenta'),
        (2, 'Szukam agenta'),
        (3, 'Nie szukam agenta')
    )

    TRAINING_READY_CHOCIES = (
        (1, '1-2 treningi'),
        (2, '3-4 treningi'),
        (3, '5-6 treningi')
    )

    team_club_league_voivodeship_ver = models.CharField(
        _('team_club_league_voivodeship_ver'),
        max_length=355,
        help_text=_('Drużyna, klub, rozgrywki, wojewódźtwo.'),
        blank=True,
        null=True,)

    club = models.CharField(
        _('Klub'),
        max_length=68,
        help_text=_('Klub w którym obecnie reprezentuejsz'),
        blank=True,
        null=True,)

    club_raw = models.CharField(
        _('Deklarowany Klub'),
        max_length=68,
        help_text=_('Klub w którym deklarujesz że obecnie reprezentuejsz'),
        blank=True,
        null=True,)

    team = models.CharField(
        _('Drużyna'),
        max_length=68,
        help_text=_('Drużyna w której obecnie grasz'),
        blank=True,
        null=True)

    team_raw = models.CharField(
        _('Deklarowana Drużyna'),
        max_length=68,
        help_text=_('Drużyna w której deklarujesz że obecnie grasz'),
        blank=True,
        null=True)

    league = models.CharField(
        _('Rozgrywki'),
        max_length=68,
        help_text=_('Poziom rozgrywkowy'),
        blank=True,
        null=True)

    league_raw = models.CharField(
        _('Rozgrywki'),
        max_length=68,
        help_text=_('Poziom rozgrywkowy który deklarujesz że grasz.'),
        blank=True,
        null=True)

    voivodeship = models.CharField(
        _('Wojewódźtwo'),
        help_text=_('Wojewódźtwo'),
        max_length=68,
        blank=True,
        null=True)

    voivodeship_raw = models.CharField(
        _('Wojewódźtwo'),
        help_text=_('Wojewódźtwo w którym grasz.'),
        max_length=68,
        blank=True,
        null=True)

    birth_date = models.DateField(
        _('Data urodzenia'),
        blank=True,
        null=True)

    height = models.PositiveIntegerField(
        _('Wzrost'),
        help_text=_('Wysokość (cm) [130-210cm]'),
        blank=True,
        null=True,
        validators=[MinValueValidator(130), MaxValueValidator(210)])

    weight = models.PositiveIntegerField(
        _('Waga'),
        help_text=_('Waga(kg) [40-140kg]'),
        blank=True,
        null=True,
        validators=[MinValueValidator(40), MaxValueValidator(140)])

    @property
    def is_goalkeeper(self):
        if self.position_raw is not None:
            return self.position_raw == 1
        return None

    position_raw = models.IntegerField(
        _('Pozycja'),
        choices=make_choices(POSITION_CHOICES),
        blank=True,
        null=True)

    position_raw_alt = models.IntegerField(
        _('Pozycja alternatywna'),
        # max_length=35,
        choices=make_choices(POSITION_CHOICES),
        blank=True,
        null=True)

    position_fantasy = models.CharField(
        _('Pozycja Fantasy'),
        max_length=35,
        blank=True,
        null=True)

    formation = models.CharField(
        _('Formacja'),
        choices=make_choices(FORMATION_CHOICES),
        max_length=15,
        null=True,
        blank=True)

    formation_alt = models.CharField(
        _('Alternatywna formacja'),
        choices=make_choices(FORMATION_CHOICES),
        max_length=15,
        null=True,
        blank=True)

    prefered_leg = models.IntegerField(
        _('Noga'),
        choices=make_choices(LEG_CHOICES),
        # max_length=30,
        null=True,
        blank=True)

    transfer_status = models.IntegerField(
        _('Status transferowy'),
        choices=make_choices(TRANSFER_STATUS_CHOICES),
        # max_length=45,
        null=True,
        blank=True)

    card = models.IntegerField(
        _('Karta na ręku'),
        choices=make_choices(CARD_CHOICES),
        # max_length=60,
        null=True,
        blank=True)

    soccer_goal = models.IntegerField(
        _('Piłkarski cel'),
        choices=make_choices(GOAL_CHOICES),
        # max_length=60,
        null=True,
        blank=True)

    phone = PhoneNumberField(
        _('Telefon'),
        blank=True,
        null=True)

    facebook_url = models.URLField(
        _('Facebook'),
        blank=True,
        null=True)

    laczynaspilka_url = models.URLField(
        _('LNP'),
        blank=True,
        null=True)

    min90_url = models.URLField(
        _('90min portal'),
        blank=True,
        null=True)

    transfermarket_url = models.URLField(
        _('TrasferMarket'),
        blank=True,
        null=True)

    address = AddressField(
        help_text=_('Adres'),
        blank=True,
        null=True)

    practice_distance = models.PositiveIntegerField(
        _('Maksymalna odległość na trening'),
        blank=True,
        null=True,
        help_text=_('Maksymalna odległośc na trening'),
        validators=[MinValueValidator(10), MaxValueValidator(500)])

    about = models.TextField(
        _('O sobie'),
        null=True,
        blank=True)

    training_ready = models.IntegerField(
        _('Gotowość do treningu'),
        choices=make_choices(TRAINING_READY_CHOCIES),
        null=True,
        blank=True)

    country = CountryField(
        _('Country'),
        blank=True,
        null=True,
        blank_label=_('Wybierz kraj'),
    )

    agent_status = models.IntegerField(_('Czy Agent'), choices=make_choices(AGENT_STATUS_CHOICES), blank=True, null=True)
    agent_name = models.CharField(_('Imię i nazwisko agenta / Nazwa agencji'), max_length=45, choices=make_choices(AGENT_STATUS_CHOICES), blank=True, null=True)
    agent_phone = PhoneNumberField(_('Numer telefonu do agenta / agencji'), blank=True, null=True)
    agent_name = models.BooleanField(_('Otwarty na propozycje zagraniczne'), blank=True, null=True)

    @property
    def age(self):
        if self.birth_date:
            now = timezone.now()
            return now.year - self.birth_date.year - ((now.month, now.day) < (self.birth_date.month, self.birth_date.day))
        else:
            return None

    @property
    def attached(self):
        return self.data_mapper_id is not None

    def calculate_data_from_data_models(self):
        if self.attached:
            adpt = PlayerAdapter(self.data_mapper_id)
            self.league = adpt.get_current_league()
            self.voivodeship = adpt.get_current_voivodeship()
            # self.club = adpt.get_current_club()  # not yet implemented. Maybe after 1.12
            self.team = adpt.get_current_team()

    def save(self, *args, **kwargs):
        ''''Nie jest wyświetlana na profilu.
        Pole wykorzystywane wyłącznie do gry Fantasy. 
        Użytkownik nie ingeruje w nie, bo ustawiony jest trigger przy wyborze pozycji z A18. 
        Bramkarz' -> 'bramkarz'; 'Obrońca%' ->  'obronca';  '%pomocnik' -> pomocnik; 'Skrzydłowy' -> 'pomocnik'; 'Napastnik' -> 'napastnik'

           POSITION_CHOICES = [
        (1, 'Bramkarz'),
        (2, 'Obrońca Lewy'),
        (3, 'Obrońca Prawy'),
        (4, 'Obrońca Środkowy'),
        (5, 'Pomocnik defensywny (6)'),
        (6, 'Pomocnik środkowy (8)'),
        (7, 'Pomocnik ofensywny (10)'),
        (8, 'Skrzydłowy'),
        (9, 'Napastnik'),
        ]
        '''
        self.calculate_data_from_data_models()

        if self.position_raw is not None:
            self.position_fantasy = self.FANTASY_MAPPING.get(self.position_raw, None)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Player Profile"
        verbose_name_plural = "Player Profiles"


class PlayerMetrics(models.Model):

    player = models.OneToOneField(
        PlayerProfile,
        on_delete=models.CASCADE,
        )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    games_summary = models.JSONField(null=True, blank=True)
    games_summary_updated = models.DateTimeField(null=True, blank=True)
    games = models.JSONField(null=True, blank=True)
    games_updated = models.DateTimeField(null=True, blank=True)

    fantasy_summary = models.JSONField(null=True, blank=True)
    fantasy_summary_updated = models.DateTimeField(null=True, blank=True)
    fantasy = models.JSONField(null=True, blank=True)
    fantasy_updated = models.DateTimeField(null=True, blank=True)

    season_summary = models.JSONField(null=True, blank=True)
    season_summary_updated = models.DateTimeField(null=True, blank=True)
    season = models.JSONField(null=True, blank=True)
    season_updated = models.DateTimeField(null=True, blank=True)

    def _update_cached_field(self, attr: str, data, commit=True):
        setattr(self, attr, data)
        setattr(self, f'{attr}_updated', datetime.now())
        if commit:
            self.save()

    def update_summaries(self, games, season, fantasy):
        self.update_games_summary(games, commit=False)
        self.update_fantasy_summary(fantasy, commit=False)
        self.update_season_summary(season)

    def update_games(self, *args, **kwargs):
        self._update_cached_field('games', *args, **kwargs)

    def update_games_summary(self, *args, **kwargs):
        self._update_cached_field('games_summary', *args, **kwargs)

    def update_fantasy(self, *args, **kwargs):
        self._update_cached_field('fantasy', *args, **kwargs)

    def update_fantasy_summary(self, *args, **kwargs):
        self._update_cached_field('fantasy_summary', *args, **kwargs)

    def update_season(self, *args, **kwargs):
        self._update_cached_field('season', *args, **kwargs)

    def update_season_summary(self, *args, **kwargs):
        self._update_cached_field('season_summary', *args, **kwargs)

    def how_old_days(self, games=False, season=False, fantasy=False, games_summary=False, season_summary=False, fantasy_summary=False):

        if games:
            date = self.games_updated
        elif games_summary:
            date = self.games_summary_updated
        elif season:
            date = self.season_updated
        elif season_summary:
            date = self.season_summary_updated
        elif fantasy:
            date = self.fantasy_updated
        elif fantasy_summary:
            date = self.fantasy_summary_updated
        else:
            date = self.updated_at

        if date is None:
            return 999
        now = timezone.now()
        diff = now - date
        return diff.days

    def save(self, data_refreshed: bool = None, *args, **kwargs):
        if data_refreshed is not None and data_refreshed is True:
            self.updated_at = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Metryka gracza")
        verbose_name_plural = _("Metryki graczy")


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
    soccer_goal = models.CharField(_('soccer goal'), choices=make_choices(GOALS_CHOICES), max_length=60, null=True, blank=True)
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
