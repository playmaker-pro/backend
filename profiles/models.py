
from collections import Counter
from datetime import datetime
from stats import adapters
from address.models import AddressField
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
# from phonenumber_field.modelfields import PhoneNumberField  # @remark: phone numbers expired
from roles import definitions
from stats.adapters import PlayerAdapter
from .utils import make_choices
from .utils import unique_slugify
import utils as utilites
from .utils import get_current_season, conver_vivo_for_api, supress_exception
from clubs import models as clubs_models


User = get_user_model()


GLOBAL_TRAINING_READY_CHOCIES = (
        (1, '1-2 treningi'),
        (2, '3-4 treningi'),
        (3, '5-6 treningi'))


class VerificationCompletionFieldsWrongSetup(Exception):
    pass


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

    new = models.CharField(max_length=100, choices=definitions.ACCOUNT_ROLES)

    class Meta:
        unique_together = ('user', 'request_date')

    def approve(self):
        self.approved = True
        self.save()

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
    counter_coach = models.PositiveIntegerField(default=0)
    counter_scout = models.PositiveIntegerField(default=0)

    def increment(self, commit=True):
        self.counter += 1
        if commit:
            self.save()

    def increment_coach(self, commit=True):
        self.counter_coach += 1
        if commit:
            self.save()

    def increment_scout(self, commit=True):
        self.counter_scout += 1
        if commit:
            self.save()


class BaseProfile(models.Model):
    """Base profile model to held most common profile elements"""
    PROFILE_TYPE = None

    AUTO_VERIFY = False  # flag to perform auto verification of User based on profile. If true - User.state will be switched to Verified

    VERIFICATION_FIELDS = []  # this is definition of profile fields which will be threaded as must-have params.

    COMPLETE_FIELDS = []  # this is definition of profile fields which will be threaded as mandatory for full profile.

    OPTIONAL_FIELDS = []  # this is definition of profile fields which will be threaded optional

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
        _("Krótki opis o sobie"),
        max_length=455,
        blank=True,
        null=True)

    def get_permalink(self):
        return reverse("profiles:show", kwargs={"slug": self.slug})

    def get_club_object(self):
        if self.PROFILE_TYPE in [definitions.PROFILE_TYPE_CLUB, definitions.PROFILE_TYPE_COACH]:
            if self.PROFILE_TYPE == definitions.PROFILE_TYPE_CLUB:
                return self.club_object
            elif self.PROFILE_TYPE == definitions.PROFILE_TYPE_COACH:
                return self.team_object.club
            # @todo: here player profile need to be added.
        else:
            return None

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
        # silent_param = kwargs.get('silent', False)
        # if silent_param is not None:
        #     kwargs.pop('silent')
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

        # if not silent_param:
        # Cases when one of verification fields is None
        if self._is_verification_fields_filled():
            if not self.user.is_waiting_for_verification and not self.user.is_verified:
                reason_text = 'Parametry weryfikacyjne są uzupełnione, a użytkownik nie miał wcześniej statusu "zwerfikowany" ani że "czeka na weryfikacje"'
                reason = f'[verification-params-ready]: \n {reason_text} \n\n params:{self.VERIFICATION_FIELDS})  \n Old:{ver_old} -> New:{ver_new} \n'
                self.user.waiting_for_verification(extra={'reason': reason})
                self.user.save()
            else:
                if self._verification_fileds_has_changed_and_was_filled(ver_old, ver_new):
                    reason_text = 'Parametry weryfikacyjne zostały zmienione i są wszyskie pola uzupełnione.'
                    reason = f'[verification-params-changed] \n {reason_text} \n\n params:{self.VERIFICATION_FIELDS}) \n Old:{ver_old} -> New:{ver_new} \n'
                    self.user.unverify(extra={'reason': reason})
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


class TrainerContact(models.Model):
    # @todo to be connected
    first_name = models.CharField(_('Imię'), max_length=255)
    last_name = models.CharField(_('Nazwisko'), max_length=255)
    season = models.CharField(_('Sezon'), max_length=255, null=True, blank=True)
    email = models.CharField(_('adres e-mail'), max_length=255, null=True, blank=True)
    phone = models.CharField(
        _('Telefon'),
        max_length=15,
        blank=True,
        null=True)
    # phone = PhoneNumberField(_('Telefon'), region='PL', blank=True, null=True)


class SoccerDisplayMixin:
    @property
    def display_club(self):
        if self.club_raw:
            return self.club_raw
        return self.club

    @property
    def display_team(self):
        if self.team_raw:
            return self.team_raw
        return self.team

    @property
    def display_league(self):
        if self.league_raw:
            return self.league_raw
        return self.league

    @property
    def display_voivodeship(self):
        if self.voivodeship_raw:
            return conver_vivo_for_api(self.voivodeship_raw)
        return conver_vivo_for_api(self.voivodeship)


class PlayerPosition(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.name}'


class PlayerProfile(BaseProfile, SoccerDisplayMixin):
    '''Player specific profile'''
    PROFILE_TYPE = definitions.PROFILE_TYPE_PLAYER

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
        'agent_foreign',
        'video_url',
        'video_title',
        'video_description',
        'video_url_second',
        'video_title_second',
        'video_description_second',
        'video_url_third',
        'video_title_third',
        'video_description_third',
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
        9: FANTASY_ATTAKER}

    LEG_CHOICES = (
        (1, 'Lewa'),
        (2, 'Prawa'),)

    TRANSFER_STATUS_CHOICES = (
        (1, 'Szukam klubu'),
        (2, 'Rozważę wszelkie oferty'),
        (3, 'Nie szukam klubu'))

    CARD_CHOICES = (
        (1, 'Mam kartę na ręku'),
        (2, 'Nie wiem czy mam kartę na ręku'),
        (3, 'Nie mam karty na ręku'))

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
        ('3-4-3', '3-4-3'))

    GOAL_CHOICES = (
        (1, 'Poziom profesjonalny'),
        (2, 'Poziom półprofesjonalny'),
        (3, 'Poziom regionalny'),)

    AGENT_STATUS_CHOICES = (
        (1, 'Mam agenta'),
        (2, 'Szukam agenta'),
        (3, 'Nie szukam agenta'))

    TRAINING_READY_CHOCIES = GLOBAL_TRAINING_READY_CHOCIES

    team_club_league_voivodeship_ver = models.CharField(
        _('team_club_league_voivodeship_ver'),
        max_length=355,
        help_text=_('Drużyna, klub, rozgrywki, wojewódźtwo.'),
        blank=True,
        null=True,)

    club = models.CharField(
        _('Klub'),
        max_length=68,
        db_index=True,
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
        db_index=True,
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
        db_index=True,
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
        db_index=True,
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
        db_index=True,
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

    # phone = PhoneNumberField(
    #     _('Telefon'),
    #     region='PL',
    #     blank=True,
    #     null=True)

    phone = models.CharField(
        _('Telefon'),
        max_length=15,
        blank=True,
        null=True)

    facebook_url = models.URLField(
        _('Facebook'),
        max_length=500,
        blank=True,
        null=True)

    laczynaspilka_url = models.URLField(
        _('LNP'),
        max_length=500,
        blank=True,
        null=True)

    min90_url = models.URLField(
        _('90min portal'),
        max_length=500,
        blank=True,
        null=True)

    transfermarket_url = models.URLField(
        _('TrasferMarket'),
        blank=True,
        null=True)

    address = AddressField(
        help_text=_('Miasto z którego dojeżdżam na trening'),
        blank=True,
        null=True)

    practice_distance = models.PositiveIntegerField(
        _('Odległość na trening'),
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
        # blank=True,
        default='PL',
        null=True,
        blank_label=_('Wybierz kraj'),
    )

    agent_status = models.IntegerField(_('Czy posiadasz agenta'), choices=make_choices(AGENT_STATUS_CHOICES), blank=True, null=True)
    agent_name = models.CharField(_('Nazwa agenta'), max_length=45, blank=True, null=True)

    agent_phone = models.CharField(
        _('Telefon do agenta'),
        max_length=15,
        blank=True,
        null=True)

    agent_foreign = models.BooleanField(_('Otwarty na propozycje zagraniczne'), blank=True, null=True)

    video_url = models.URLField(
        _('Youtube url'),
        blank=True,
        null=True)
    video_title = models.CharField(
        _('Tytuł nagrania'), max_length=235, blank=True, null=True)

    video_description = models.TextField(
        _('Temat i opis'),
        null=True,
        blank=True)

    video_url_second = models.URLField(
        _('Youtube url nr 2'),
        blank=True,
        null=True)

    video_title_second = models.CharField(
        _('Tytuł nagrania nr 2'), max_length=235, blank=True, null=True)

    video_description_second = models.TextField(
        _('Temat i opis nr 2'),
        null=True,
        blank=True)

    video_url_third = models.URLField(
        _('Youtube url nr 3'),
        blank=True,
        null=True)

    video_title_third = models.CharField(
        _('Tytuł nagrania nr 3'), max_length=235, blank=True, null=True)

    video_description_third = models.TextField(
        _('Temat i opis nagrania nr 3'),
        null=True,
        blank=True)

    @property
    def age(self):  # todo przeniesc to do uzywania z profile.utils.
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
            if adpt.has_player:
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

        before_datamapper = self.data_mapper_id

        if self.position_raw is not None:
            self.position_fantasy = self.FANTASY_MAPPING.get(self.position_raw, None)
        super().save(*args, **kwargs)

        after_datamapper = self.data_mapper_id
        if before_datamapper is None and after_datamapper is not None:
            self.playermetrics.refresh_metrics()

    class Meta:
        verbose_name = "Player Profile"
        verbose_name_plural = "Player Profiles"


class PlayerMetrics(models.Model):
    # @todo tu powinna isc metoda    u.profile.playermetrics.refresh()
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

    def refresh_metrics(self):
        if not self.player.has_data_id:
            return
        season_name = get_current_season()
        _id = self.player.data_mapper_id

        fantasy = adapters.PlayerFantasyDataAdapter(_id).get(season=season_name, full=True)
        self.update_fantasy(fantasy)

        season = adapters.PlayerStatsSeasonAdapter(_id).get(groupped=True)
        self.update_season(season)

        games = adapters.PlayerLastGamesAdapter(_id).get()
        self.update_games(games)

        games_summary = adapters.PlayerLastGamesAdapter(_id).get(season=season_name, limit=3)  # should be profile.playermetrics.refresh_games_summary() and putted to celery.
        fantasy_summary = adapters.PlayerFantasyDataAdapter(_id).get(season=season_name)
        season_summary = adapters.PlayerStatsSeasonAdapter(_id).get(season=season_name)
        self.update_summaries(games_summary, season_summary, fantasy_summary)
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


class ClubProfile(BaseProfile, SoccerDisplayMixin):
    PROFILE_TYPE = definitions.PROFILE_TYPE_CLUB

    CLUB_ROLE = (
        (1, 'Prezes'),
        (2, 'Kierownik'),
        (3, 'Członek zarządu'),
        (4, 'Sztab szkoleniowy'),
        (5, 'Inne'))

    VERIFICATION_FIELDS = [
        'team_club_league_voivodeship_ver',
        'club_role',
    ]

    @property
    @supress_exception
    def display_club(self):
        return self.club_object.display_club

    @property
    @supress_exception
    def display_voivodeship(self):
        return self.club_object.display_voivodeship

    club_object = models.ForeignKey(
        clubs_models.Club,
        on_delete=models.SET_NULL,
        related_name='clubowners',
        db_index=True,
        null=True,
        blank=True
    )

    # phone = PhoneNumberField(
    #     _('Telefon'),
    #     region='PL',
    #     blank=True,
    #     null=True)

    phone = models.CharField(
        _('Telefon'),
        max_length=15,
        blank=True,
        null=True)

    team_club_league_voivodeship_ver = models.CharField(
        _('team_club_league_voivodeship_ver'),
        max_length=355,
        help_text=_('Drużyna, klub, rozgrywki, wojewódźtwo.'),
        blank=True,
        null=True,)

    club_role = models.IntegerField(
        choices=CLUB_ROLE,
        null=True, blank=True,
        help_text='Defines if admin approved change')   

    class Meta:
        verbose_name = "Club Profile"
        verbose_name_plural = "Club Profiles"


class CoachProfile(BaseProfile, SoccerDisplayMixin):
    PROFILE_TYPE = definitions.PROFILE_TYPE_COACH

    COMPLETE_FIELDS = ['phone']

    CLUB_ROLE = (
        (1, 'Trener'),
        (2, 'Prezes'),
        (3, 'Kierownik'),
        (4, 'Członek zarządu'),
        (5, 'Sztab szkoleniowy'),
        (6, 'Inne')
    )

    VERIFICATION_FIELDS = [
        'country',
        'birth_date',
        'team_club_league_voivodeship_ver']

    OPTIONAL_FIELDS = ['licence']

    GOAL_CHOICES = (
        (1, 'Profesjonalna kariera'),
        (2, 'Kariera regionalna'),
        (3, 'Trenerka jako hobby'),)
    # fields = ["league", "voivodeship", "team", "country", "address", "about", "birth_date", "facebook_url", "soccer_goal", "phone", "practice_distance"]

    TRAINING_READY_CHOCIES = GLOBAL_TRAINING_READY_CHOCIES

    @property
    @supress_exception
    def display_club(self):
        return self.team_object.club.display_club

    @property
    @supress_exception
    def display_team(self):
        return self.team_object.display_team

    @property
    @supress_exception
    def display_seniority(self):
        return self.team_object.display_seniority

    @property
    @supress_exception
    def display_gender(self):
        return self.team_object.display_gender

    @property
    @supress_exception
    def display_voivodeship(self):
        return self.team_object.club.display_voivodeship

    @property
    @supress_exception
    def display_league(self):
        return self.team_object.display_league

    LICENCE_CHOICES = (
        (1, 'UEFA PRO'),
        (2, 'UEFA A'),
        (3, 'UEFA EY A'),
        (4, 'UEFA B'),
        (5, 'UEFA C'),
        (6, 'GRASS C'),
        (7, 'GRASS D'),
        (8, 'UEFA Futsal B'),
        (9, 'PZPN A'),
        (10, 'PZPN B'),
        (11, 'W trakcie kursu'),
    )

    licence = models.IntegerField(
        _("Licencja"),
        choices=LICENCE_CHOICES,
        blank=True,
        null=True)

    team_club_league_voivodeship_ver = models.CharField(
        _('team_club_league_voivodeship_ver'),
        max_length=355,
        help_text=_('Drużyna, klub, rozgrywki, wojewódźtwo.'),
        blank=True,
        null=True,)

    team_object = models.ForeignKey(
        clubs_models.Team,
        on_delete=models.SET_NULL,
        related_name='coaches',
        null=True,
        blank=True
    )

    birth_date = models.DateField(
        _('Data urodzenia'),
        blank=True,
        null=True)

    soccer_goal = models.IntegerField(
        _('Piłkarski cel'),
        choices=make_choices(GOAL_CHOICES),
        # max_length=60,
        null=True,
        blank=True)
    # phone = PhoneNumberField(
    #     _('Telefon'),
    #     region='PL',
    #     blank=True,
    #     null=True)
    phone = models.CharField(
        _('Telefon'),
        max_length=15,
        blank=True,
        null=True)
    facebook_url = models.URLField(
        _('Facebook'),
        max_length=500,
        blank=True,
        null=True)
    country = CountryField(
        _('Country'),
        blank=True,
        default='PL',
        null=True,
        blank_label=_('Wybierz kraj'),)

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

    address = AddressField(
        help_text=_('Adres'),
        blank=True,
        null=True)
    # club & coach specific attrs.

    club_role = models.IntegerField(
        choices=CLUB_ROLE,
        default=1,  # trener
        null=True, blank=True,
        help_text='Defines if admin approved change')

    @property
    def age(self):  # todo przeniesc to do uzywania z profile.utils.
        if self.birth_date:
            now = timezone.now()
            return now.year - self.birth_date.year - ((now.month, now.day) < (self.birth_date.month, self.birth_date.day))
        else:
            return None

    class Meta:
        verbose_name = "Coach Profile"
        verbose_name_plural = "Coaches Profiles"


class GuestProfile(BaseProfile):   # @todo to be removed
    PROFILE_TYPE = definitions.PROFILE_TYPE_GUEST
    AUTO_VERIFY = True
    facebook_url = models.URLField(
        _('Facebook'),
        max_length=500,
        blank=True,
        null=True)

    class Meta:
        verbose_name = "Guest Profile"
        verbose_name_plural = "Guests Profiles"


class ManagerProfile(BaseProfile):
    PROFILE_TYPE = definitions.PROFILE_TYPE_MANAGER
    AUTO_VERIFY = True
    facebook_url = models.URLField(
        _('Facebook'),
        max_length=500,
        blank=True,
        null=True)

    class Meta:
        verbose_name = "Manager Profile"
        verbose_name_plural = "Managers Profiles"


class ParentProfile(BaseProfile):
    PROFILE_TYPE = definitions.PROFILE_TYPE_PARENT
    AUTO_VERIFY = True
    facebook_url = models.URLField(
        _('Facebook'),
        max_length=500,
        blank=True,
        null=True)

    class Meta:
        verbose_name = "Parent Profile"
        verbose_name_plural = "Parents Profiles"


class ScoutProfile(BaseProfile):
    PROFILE_TYPE = definitions.PROFILE_TYPE_SCOUT
    AUTO_VERIFY = True
    VERIFICATION_FIELDS = []

    COMPLETE_FIELDS = [
        'soccer_goal']

    OPTIONAL_FIELDS = [
        'country',
        'facebook_url',
        'address',
        'practice_distance',
        'club_raw',
        'league_raw',
        'voivodeship_raw',
        ]

    GOAL_CHOICES = (
        (1, 'Profesjonalna kariera'),
        (2, 'Kariera regionalna'),
        (3, 'Skauting jako hobby'))

    soccer_goal = models.IntegerField(
        _('Piłkarski cel'),
        choices=make_choices(GOAL_CHOICES),
        # max_length=60,
        null=True,
        blank=True)
    country = CountryField(
        _('Country'),
        default='PL',
        blank=True,
        null=True,
        blank_label=_('Wybierz kraj'),)
    facebook_url = models.URLField(
        _('Facebook'),
        max_length=500,
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

    club = models.CharField(
        _('Klub'),
        max_length=68,
        help_text=_('Klub, który obecnie reprezentuejsz'),
        blank=True,
        null=True,)

    club_raw = models.CharField(
        _('Deklarowany klub'),
        max_length=68,
        help_text=_('Klub w którym obecnie reprezentuejsz'),
        blank=True,
        null=True,)

    league = models.CharField(
        _('Rozgrywki'),
        max_length=68,
        help_text=_('Poziom rozgrywkowy'),
        blank=True,
        null=True)

    league_raw = models.CharField(
        _('Deklarowany poziom rozgrywkowy'),
        max_length=68,
        help_text=_('Poziom rozgrywkowy'),
        blank=True,
        null=True)

    voivodeship = models.CharField(
        _('Wojewódźtwo'),
        help_text=_('Wojewódźtwo'),
        max_length=68,
        blank=True,
        null=True)

    voivodeship_raw = models.CharField(
        _('Deklarowane wojewódźtwo'),
        help_text=_('Wojewódźtwo w którym grasz.'),
        max_length=68,
        blank=True,
        null=True)

    class Meta:
        verbose_name = "Scout Profile"
        verbose_name_plural = "Scouts Profiles"
