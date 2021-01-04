import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.urls import reverse
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
from address.models import AddressField
from profiles.utils import unique_slugify, conver_vivo_for_api, supress_exception
from django_countries.fields import CountryField


class Voivodeship(models.Model):
    name = models.CharField(max_length=455, unique=True)

    @property
    def display_voivodeship(self):
        return self.name

    def __str__(self):
        return f'{self.name}'


class Club(models.Model):
    PROFILE_TYPE = 'klub'

    manager = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name='managed_club',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
        )

    editors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='club_managers',
        blank=True
        )

    voivodeship = models.ForeignKey(
        Voivodeship,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def is_editor(self, user):
        if user == self.manager or user in self.editors.all():
            return True
        else:
            return False

    @property
    @supress_exception
    def display_manager(self):
        return self.manager.get_full_name()

    @property
    @supress_exception
    def display_club(self):
        if self.club_raw:
            return self.club_raw
        return self.name

    @property
    @supress_exception
    def display_voivodeship(self):
        if self.voivodeship_raw:
            return conver_vivo_for_api(self.voivodeship_raw)
        return conver_vivo_for_api(self.voivodeship.name)

    picture = models.ImageField(
        _("Zdjęcie"),
        upload_to="club_pics/%Y-%m-%d/",
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

    name = models.CharField(
        _('Club name'),
        max_length=255,
        help_text='Displayed Name of club')

    club_raw = models.CharField(
        _('Deklarowany Klub'),
        max_length=255,
        help_text=_('Klub w którym deklarujesz że obecnie reprezentuejsz'),
        blank=True,
        null=True,)

    voivodeship_raw = models.CharField(
        _('Wojewódźtwo'),
        help_text=_('Wojewódźtwo w którym grasz.'),
        max_length=255,
        blank=True,
        null=True)

    country = CountryField(
        _('Kraj'),
        # blank=True,
        default='PL',
        null=True,
        blank_label=_('Wybierz kraj'),
    )

    def get_permalink(self):
        return reverse("clubs:show_club", kwargs={"slug": self.slug})

    class Meta:
        verbose_name = _('Klub')
        verbose_name_plural = _('Kluby')

    def __str__(self):
        return f'{self.name}'

    # club_phone = PhoneNumberField(
    #     _('Telefon'),
    #     blank=True,
    #     null=True)

    club_phone = models.CharField(
        _('Telefon'),
        max_length=15,
        blank=True,
        null=True)

    club_email = models.EmailField(null=True, blank=True)

    stadion_address = AddressField(
        related_name='coach_stadion_address',
        help_text=_('Adres'),
        blank=True,
        null=True)

    practice_stadion_address = AddressField(
        related_name='coach_practice_stadion_address',
        help_text=_('Adres'),
        blank=True,
        null=True)

    def save(self, *args, **kwargs):
        slug_str = "%s %s" % (self.PROFILE_TYPE, self.name)
        unique_slugify(self, slug_str)
        super().save(*args, **kwargs)


class League(models.Model):
    name = models.CharField(max_length=355, unique=True)

    @property
    def display_league(self):
        return self.name

    def __str__(self):
        return f'{self.name}'


class Seniority(models.Model):
    name = models.CharField(max_length=355, unique=True)

    @property
    def display_seniority(self):
        return self.name

    def __str__(self):
        return f'{self.name}'


class Gender(models.Model):
    name = models.CharField(max_length=355, unique=True)

    @property
    def display_gender(self):
        return self.name

    def __str__(self):
        return f'{self.name}'


class Team(models.Model):
    PROFILE_TYPE = 'team'

    EDITABLE_FIELDS = [
        'name',
        'picture',
        'travel_refunds',
        'game_bonus',
        'scolarships',
        'gloves_shoes_refunds',
        'traning_gear',
        'regular_gear',
        'secondary_trainer',
        'fizo',
        'diet_suplements'
    ]
    gender = models.ForeignKey(
        Gender,
        on_delete=models.SET_NULL,
        null=True,
        blank=True)

    league = models.ForeignKey(
        League,
        on_delete=models.SET_NULL,
        null=True,
        blank=True)

    seniority = models.ForeignKey(
        Seniority,
        on_delete=models.SET_NULL,
        null=True,
        blank=True)

    editors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='teammanagers',
        blank=True
    )

    manager = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='managed_team',
        null=True,
        blank=True
    )

    slug = models.CharField(
        max_length=255,
        blank=True,
        editable=False)

    picture = models.ImageField(
        _("Zdjęcie"),
        upload_to="team_pics/%Y-%m-%d/",
        null=True,
        blank=True)

    club = models.ForeignKey(
        Club,
        related_name='teams',
        null=True,
        on_delete=models.SET_NULL,
    )

    data_mapper_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='ID of object placed in data_ database. It should alwayes reflect scheme which represents.')

    def is_editor(self, user):
        if user == self.manager or user in self.editors.all():
            return True
        else:
            return False
    
    @property
    def display_team(self):
        return self.name

    @property
    @supress_exception
    def display_coach(self):
        return self.manager.get_full_name()

    @property
    @supress_exception
    def display_club(self):
        return self.club.display_club

    @property
    @supress_exception
    def display_voivodeship(self):
        return self.club.display_voivodeship

    @property
    @supress_exception
    def display_league(self):
        return self.league.display_league

    @property
    @supress_exception
    def display_seniority(self):
        return self.seniority.display_seniority

    @property
    @supress_exception
    def display_gender(self):
        return self.gender.display_gender

    name = models.CharField(
        _('Team name'),
        max_length=255,
        help_text='Displayed Name of team')

    def get_permalink(self):
        return reverse("clubs:show_team", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        slug_str = "%s %s %s" % (self.PROFILE_TYPE, self.name, self.club.name)
        unique_slugify(self, slug_str)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Team')
        verbose_name_plural = _("Teams")
        unique_together = ('name', 'club')


    # common  team fileds
    travel_refunds = models.BooleanField(
        _('Zwrot za dojazdy'),
        default=False)

    game_bonus = models.BooleanField(
        _('Premie za mecze'),
        default=False,)

    scolarships = models.BooleanField(
        _('Stypendia'),
        default=False,
        )

    gloves_shoes_refunds = models.BooleanField(
        _('Zwroty za buty/rękawice'),
        default=False,
        )

    traning_gear = models.BooleanField(
        _('Sprzęt treningowy'),
        default=False,
        )

    regular_gear = models.BooleanField(
        _('Sprzęt wyjściowy'),
        default=False,
        )

    secondary_trainer = models.BooleanField(
        _('Drugi trener'),
        default=False,
        )

    fizo = models.BooleanField(
        _('Fizjoterapeuta'),
        default=False,
        )

    diet_suplements = models.BooleanField(
        _('Suplemnety / odżywki'),
        default=False,
        )

    def __str__(self):
        return f'{self.name}'
