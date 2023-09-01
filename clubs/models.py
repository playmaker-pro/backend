from functools import cached_property, lru_cache
from typing import List, Union

from address.models import AddressField
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField

from external_links.models import ExternalLinks
from mapper.models import Mapper
from profiles.utils import conver_vivo_for_api, supress_exception, unique_slugify
from voivodeships.models import Voivodeships

from .managers import LeagueManager


class Season(models.Model):
    name = models.CharField(max_length=9, unique=True)
    is_current = models.BooleanField(null=True, blank=True)
    is_in_verify_form = models.BooleanField(default=True)

    @classmethod
    def define_current_season(self, date=None) -> str:
        """
        JJ:
        Definicja aktualnego sezonu
        (wyznaczamy go za pomocą:
            jeśli miesiąc daty systemowej jest >= 7 to pokaż sezon (aktualny rok/ aktualny rok + 1).
            Jeśli < 7 th (aktualny rok - 1 / aktualny rok)
        """
        season_middle = settings.SEASON_DEFINITION.get("middle", 7)
        if date is None:
            date = timezone.now()

        if date.month >= season_middle:
            season = f"{date.year}/{date.year + 1}"
        else:
            season = f"{date.year - 1}/{date.year}"
        return season

    class Meta:
        ordering = ("-is_current",)

    def current_season_update(self, *args, **kwargs):
        current_season = self.define_current_season()
        for season in self._meta.model.objects.all():
            season.is_current = season.name == current_season
            season.save(updated=True)

    def save(self, updated=False, *args, **kwargs):
        super().save(*args, **kwargs)
        if not updated:
            self.current_season_update()

    @property
    def display_season(self):
        return self.name

    def __str__(self):
        return f"{self.name}"


class Voivodeship(models.Model):
    name = models.CharField(max_length=455, unique=True)

    @property
    def display_voivodeship(self):
        return self.name

    def __str__(self):
        return f"{self.name}"


def remove_polish_chars(filename):
    return (
        filename.replace("ł", "l")
        .replace("ą", "a")
        .replace("ó", "o")
        .replace("ż", "z")
        .replace("ź", "z")
        .replace("ń", "n")
        .replace("ę", "e")
        .replace("ś", "s")
        .replace("ć", "c")
    )


class MappingMixin:
    def get_mapped_names(self):
        if self.mapping:
            if isinstance(self.mapping, str):
                return [name.strip() for name in self.mapping.split(",") if name]
        return None


class Club(models.Model, MappingMixin):
    PROFILE_TYPE = "klub"

    autocreated = models.BooleanField(default=False, help_text="Autocreated from s38")

    mapping = models.TextField(
        null=True,
        blank=True,
        help_text='Mapping names comma separated. eg "name X", "name Xi"',
    )

    mapper = models.OneToOneField(
        Mapper, on_delete=models.SET_NULL, blank=True, null=True
    )

    external_links = models.OneToOneField(
        ExternalLinks, on_delete=models.SET_NULL, blank=True, null=True
    )

    manager = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="managed_club",
        null=True,
        blank=True,
    )

    editors = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="club_managers", blank=True
    )

    # TODO Based on task PM-363. After migration on production, field can be deleted
    voivodeship = models.ForeignKey(
        Voivodeship,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Województwo"),
        help_text="Wybierz województwo. Stare pole, czeka na migracje",
    )
    voivodeship_obj = models.ForeignKey(
        Voivodeships,
        verbose_name=_("Województwo"),
        help_text="Wybierz województwo.",
        max_length=20,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
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
        return self.name

    @property
    @supress_exception
    def display_voivodeship(self):
        return conver_vivo_for_api(self.voivodeship_obj.name)

    def get_file_path(instance, filename):
        """Replcae server language code mapping"""
        return f"club_pics/%Y-%m-%d/{remove_polish_chars(filename)}"

    picture = models.ImageField(
        _("Herb klubu"), upload_to=get_file_path, null=True, blank=True
    )

    data_mapper_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="ID of object placed in data_ database. It should alwayes reflect scheme which represents.",
    )

    scrapper_autocreated = models.BooleanField(
        default=False, help_text="Autocreated from new scrapper"
    )

    slug = models.CharField(max_length=255, blank=True, editable=False)

    name = models.CharField(
        _("Club name"), max_length=255, help_text="Displayed Name of club"
    )

    voivodeship_raw = models.CharField(
        _("Województwo"),
        help_text=_("Wojewódźtwo w którym grasz."),
        max_length=255,
        blank=True,
        null=True,
    )  # TODO:(l.remkowicz): followup needed to see if that can be safely removed from database scheme follow-up: PM-365

    country = CountryField(
        _("Kraj"),
        # blank=True,
        default="PL",
        null=True,
        blank_label=_("Wybierz kraj"),
    )

    club_phone = models.CharField(_("Telefon"), max_length=15, blank=True, null=True)

    club_email = models.EmailField(null=True, blank=True)
    stadion_address = AddressField(
        related_name="coach_stadion_address",
        help_text=_("Adres"),
        blank=True,
        null=True,
    )
    practice_stadion_address = AddressField(
        related_name="coach_practice_stadion_address",
        help_text=_("Adres"),
        blank=True,
        null=True,
    )

    def get_permalink(self):
        return reverse("clubs:show_club", kwargs={"slug": self.slug})

    class Meta:
        verbose_name = _("Klub")
        verbose_name_plural = _("Kluby")

    def __str__(self):
        vivo_str = f", {self.voivodeship_obj}" if self.voivodeship_obj else ""
        return f"{self.name} {vivo_str}"

    def create_mapper_obj(self):
        self.mapper = Mapper.objects.create()

    def create_external_links_obj(self):
        self.external_links = ExternalLinks.objects.create()

    def save(self, *args, **kwargs):
        slug_str = "%s %s" % (self.PROFILE_TYPE, self.name)

        if not self.mapper:
            self.create_mapper_obj()

        if not self.external_links:
            self.create_external_links_obj()

        unique_slugify(self, slug_str)
        super().save(*args, **kwargs)


class LeagueHistory(models.Model):
    season = models.ForeignKey(
        "Season", on_delete=models.SET_NULL, null=True, blank=True
    )

    index = models.CharField(max_length=255, null=True, blank=True)
    league = models.ForeignKey(
        "League", on_delete=models.CASCADE, related_name="historical"
    )
    visible = models.BooleanField(default=True)
    is_table_data = models.BooleanField(default=False)
    is_matches_data = models.BooleanField(default=False)
    data = models.JSONField(null=True, blank=True)
    data_updated = models.DateTimeField(auto_now=True)
    mapper = models.OneToOneField(
        Mapper, on_delete=models.SET_NULL, blank=True, null=True
    )
    external_links = models.OneToOneField(
        ExternalLinks, on_delete=models.SET_NULL, blank=True, null=True
    )

    league_name_raw = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="League(play) name straight from scrapped object",
    )

    def __str__(self):
        return f"{self.season} ({self.league}) {self.index or ''}"

    def create_mapper_obj(self):
        self.mapper = Mapper.objects.create()

    def create_external_links_obj(self):
        self.external_links = ExternalLinks.objects.create()

    # DEPRECATED: PM-1015
    # def check_and_set_if_data_exists(self):
    #     from data.models import League as Dleague
    #
    #     url = Dleague.get_url_based_on_id(self.index)
    #     l = Dleague.objects.get(_url=url)
    #     if l.advanced_json:
    #         self.is_table_data = True
    #     if l.games_snapshot:
    #         self.is_matches_data = True

    def get_admin_url(self):
        return reverse(
            f"admin:{self._meta.app_label}_{self._meta.model_name}_change",
            args=(self.id,),
        )

    def save(self, *args, **kwargs):
        # self.check_and_set_if_data_exists()
        self.league.set_league_season([self.season])

        if not self.mapper:
            self.create_mapper_obj()

        if not self.external_links:
            self.create_external_links_obj()

        super().save(*args, **kwargs)

    def reset(self):
        self.data = None
        self.save()


class LeagueGroup(models.Model):
    name = models.CharField(max_length=25)
    level = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name}"


class Region(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"


class JuniorLeague(models.Model):
    name = models.CharField(max_length=255)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name}"


class SectionGrouping(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"


class League(models.Model):
    name = models.CharField(max_length=355, help_text="eg. Ekstraklasa")
    virtual = models.BooleanField(default=False)
    visible = models.BooleanField(
        default=False, help_text="Determine if that league will be visible"
    )

    data_seasons = models.ManyToManyField("Season", blank=True)

    section = models.ForeignKey(
        "SectionGrouping", on_delete=models.SET_NULL, null=True, blank=True
    )
    order = models.IntegerField(default=0)

    group = models.ForeignKey(
        "LeagueGroup", on_delete=models.SET_NULL, null=True, blank=True
    )
    region = models.ForeignKey(
        "Region", on_delete=models.SET_NULL, null=True, blank=True
    )
    city_name = models.CharField(max_length=255, null=True, default=None, blank=True)

    code = models.CharField(_("league_code"), null=True, blank=True, max_length=5)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="childs",
    )
    highest_parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, blank=True, null=True
    )
    country = CountryField(
        _("Kraj"),
        default="PL",
        null=True,
        blank_label=_("Wybierz kraj"),
    )
    gender = models.ForeignKey(
        "Gender", default=None, on_delete=models.SET_NULL, null=True, blank=True
    )
    seniority = models.ForeignKey(
        "Seniority", default=None, on_delete=models.SET_NULL, null=True, blank=True
    )

    name_junior = models.ForeignKey(
        "JuniorLeague", on_delete=models.SET_NULL, null=True, blank=True, default=None
    )

    rw = models.BooleanField(default=False, help_text="Spring round (runda wiosenna)")
    # auto calculated fields & flags
    slug = models.CharField(max_length=255, blank=True, editable=False)
    isparent = models.BooleanField(default=False)

    zpn = models.CharField(max_length=255, null=True, blank=True)
    # @todo(rkesik): zpn mapped looks like deprecated. Shall we remove that?
    zpn_mapped = models.CharField(max_length=255, null=True, blank=True)
    index = models.CharField(max_length=255, null=True, blank=True)

    search_tokens = models.CharField(max_length=255, null=True, blank=True)

    scrapper_autocreated = models.BooleanField(default=False)

    def has_season_data(self, season_name: str) -> bool:
        """Just a helper function to know if historical object has data for given season"""
        if self.historical.filter(season__name=season_name).count() == 0:
            return False
        return True

    def get_file_path(instance, filename):
        return f"league_pics/%Y-%m-%d/{remove_polish_chars(filename)}"

    picture = models.ImageField(
        _("Zdjęcie"), upload_to=get_file_path, null=True, blank=True
    )

    objects = LeagueManager()

    @cached_property
    def get_childs(self):
        return self.childs.all().order_by("name")

    @cached_property
    def get_data_seasons(self):
        return self.data_seasons.all()

    @cached_property
    def is_parent(self):
        """If has no parent and have children"""
        return self.parent is None and self.get_childs.count() != 0

    @cached_property
    def standalone(self):
        """If has no parent and represents own data"""
        return self.parent is None and self.childs.all().count() == 0

    @cached_property
    def childs_ids(self) -> list:
        id_list = []
        if self.childs:
            id_list = id_list + list(self.get_childs.values_list("id", flat=True))
            for child in self.get_childs:
                id_list = id_list + child.childs_ids
        return id_list

    @cached_property
    def display_league(self) -> str:
        return self.name

    @property
    def display_name_junior(self) -> str:
        if self.name_junior and not self.name_junior.name.isspace():
            return self.name_junior.name

    @cached_property
    def display_league_top_parent(self) -> str:
        if self.highest_parent:
            return self.highest_parent.display_league

    @lru_cache
    def get_highest_parent(self):
        """Loops to find last (top) parent in a tree"""
        if self.parent:
            parent = self.parent
        else:
            return self
        while True:
            if parent.parent is None:
                return parent
            else:
                parent = parent.parent
                continue
            break

    @cached_property
    @supress_exception
    def display_league_seniority_name(self):
        return self.seniority.name

    @cached_property
    @supress_exception
    def display_league_group_name(self):
        return self.group.name

    @cached_property
    @supress_exception
    def display_league_voivodeship(self):
        return self.zpn

    def get_permalink(self):
        return (
            reverse("plays:summary", kwargs={"slug": self.slug})
            if settings.SCRAPPER
            else "#"
        )

    def get_slug_value(self):
        return self.get_upper_parent_names(spliter="--")

    def save(self, *args, **kwargs):
        # is a virtual parent?
        if self.is_parent:
            # isparent flag is due to historical reasons
            self.isparent = True
            # virtual set to true it means that this is an virtual group
            # and do not contains any league data.
            self.virtual = True

        # We set a new/modify parent attribute
        # so we need to trigger our parent object
        # to recalclate data and set a proper flag.
        if self.parent is not None:
            self.parent.isparent = True
            self.parent.save()

        unique_slugify(self, self.get_slug_value())
        # make search index
        self.search_tokens = self.build_search_tokens()
        super().save(*args, **kwargs)

    def get_upper_parent_names(self, spliter=", "):
        name = self.name
        if self.parent:
            name = (
                f"{self.parent.get_upper_parent_names(spliter=spliter)}{spliter}{name}"
            )
        return name

    def set_league_season(self, seasons: List[Season]):
        """Mechanism to set and propagate changes in data seasons."""
        self.data_seasons.add(*seasons)
        if self.parent:
            self.parent.set_league_season(list(self.data_seasons.all()))

    def build_search_tokens(self):
        """Creates string which will be used to text based searches
        `name  region city_name group.name`
        """
        group_name = self.group.name if self.group else ""
        fields = [self.name, self.zpn, self.city_name, group_name]
        return " ".join(filter(None, fields))

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.parent and self.id == self.parent.id:
            raise ValidationError({"parent": ["You cant have yourself as a parent!"]})

    def __str__(self):
        return f"{self.get_upper_parent_names()}"

    class Meta:
        unique_together = ("name", "country", "parent")
        ordering = ("order", "section__name")


class Seniority(models.Model):
    name = models.CharField(max_length=355, unique=True)
    is_senior = models.BooleanField(default=True)

    @property
    def display_seniority(self):
        return self.name

    def __str__(self):
        return f"{self.name}"


class Gender(models.Model):
    MALE = "M"
    FEMALE = "F"

    name = models.CharField(max_length=355, unique=True)

    @property
    def display_gender(self):
        return self.name

    def __str__(self):
        return f"{self.name}"

    @classmethod
    def get_male_object(cls) -> "Gender":
        """Get Gender male object"""
        return cls.objects.get(name__istartswith="m")

    @classmethod
    def get_female_object(cls) -> "Gender":
        """Get Gender female object"""
        return cls.objects.get(name__istartswith="k")


class Team(models.Model, MappingMixin):
    PROFILE_TYPE = "team"

    EDITABLE_FIELDS = [
        "name",
        "travel_refunds",
        "game_bonus",
        "scolarships",
        "gloves_shoes_refunds",
        "traning_gear",
        "regular_gear",
        "secondary_trainer",
        "fizo",
        "diet_suplements",
    ]

    mapping = models.TextField(
        null=True,
        blank=True,
        help_text='!Always keep double commna at the end of each name!!!. Mapping names comma separated. eg "name X,,name Xi,,"',
    )
    visible = models.BooleanField(default=True, help_text="Visible on database")
    autocreated = models.BooleanField(default=False, help_text="Autocreated from s38")
    gender = models.ForeignKey(Gender, on_delete=models.SET_NULL, null=True, blank=True)

    # That would be deprecated since TeamHistory introduction
    league = models.ForeignKey(League, on_delete=models.SET_NULL, null=True, blank=True)

    seniority = models.ForeignKey(
        Seniority, on_delete=models.SET_NULL, null=True, blank=True
    )

    editors = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="teammanagers", blank=True
    )

    manager = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="managed_team",
        null=True,
        blank=True,
    )

    mapper = models.OneToOneField(
        Mapper, on_delete=models.SET_NULL, blank=True, null=True
    )

    external_links = models.OneToOneField(
        ExternalLinks, on_delete=models.SET_NULL, blank=True, null=True
    )

    slug = models.CharField(max_length=255, blank=True, editable=False)

    def get_file_path(instance, filename):
        return f"team_pics/%Y-%m-%d/{remove_polish_chars(filename)}"

    club = models.ForeignKey(
        Club,
        related_name="teams",
        null=True,
        on_delete=models.SET_NULL,
    )

    data_mapper_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="ID of object placed in data_ database. It should always reflect scheme which represents.",
    )

    scrapper_autocreated = models.BooleanField(
        default=False, help_text="Auto-created from new scrapper"
    )

    junior_group = models.ForeignKey(
        "JuniorAgeGroup", null=True, blank=True, on_delete=models.SET_NULL
    )

    @property
    def should_be_visible(self):
        return (self.manager or self.club.manager) and (
            (self.seniority and self.seniority.is_senior) or not self.seniority
        )

    @property
    def get_club_pic(self):
        if self.club:
            return self.club.picture.url
        return settings.DEFAULT_CLUB_IMAGE_PATH

    def is_editor(self, user):
        if user == self.manager or user in self.editors.all():
            return True
        else:
            return False

    @property
    def latest_league_from_lh(self):
        ths = self.get_latest_team_history()
        if ths:
            return ths.league_history.league

    @property
    def team_name_with_current_league(self):
        return self.display_team + (
            " " + f"({self.latest_league_from_lh})"
            if self.latest_league_from_lh
            else ""
        )

    @property
    def league_with_parents(self):
        return self.league.get_upper_parent_names(spliter=", ")

    @property
    def name_with_league_full(self):
        return f"{self.name}" + (
            f" ({self.league_with_parents})" if self.league else ""
        )

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

    def get_latest_team_history(self) -> List["TeamHistory"]:
        sorted_team_histories = self.historical.all().order_by(
            "-league_history__season__name"
        )
        if sorted_team_histories:
            return sorted_team_histories.first()

    @property
    @supress_exception
    def display_league_top_parent(self):
        th = self.get_latest_team_history()
        if th:
            return th.league_history.league.display_league_top_parent
        return self.league.display_league_top_parent

    @property
    @supress_exception
    def display_league_seniority_name(self):
        return self.league.display_league_seniority_name

    @property
    def display_name_junior(self):
        if self.league:
            return self.league.display_name_junior

    @property
    @supress_exception
    def display_league_group_name(self):
        return self.league.display_league_group_name

    @property
    @supress_exception
    def display_league_region_and_group_name(self) -> Union[str, None]:
        region = self.league.region if self.league and self.league.region else ""
        group_name = self.league.display_league_group_name

        if region and not group_name:
            return region
        elif not region and group_name:
            return group_name
        elif region and group_name:
            return f"{group_name}, {region}"
        else:
            return None

    @property
    @supress_exception
    def display_league_voivodeship(self):
        return self.league.display_league_voivodeship

    @property
    @supress_exception
    def get_league_permalink(self):
        return self.league.get_permalink

    @property
    @supress_exception
    def display_seniority(self):
        return self.seniority.display_seniority

    @property
    @supress_exception
    def display_gender(self):
        return self.gender.display_gender

    name = models.CharField(
        _("Nazwa drużyny"),
        max_length=255,
    )

    def get_permalink(self):
        return reverse("clubs:show_team", kwargs={"slug": self.slug})

    def get_pretty_name(self):
        region_name = (
            self.league.region.name if self.league and self.league.region else ""
        )
        league_name = self.full_name
        if not league_name:
            suffix = ""
        else:
            suffix = f"({league_name}"
            if region_name:
                suffix += f", {region_name})"
            else:
                suffix += ")"

        return f"{self.name} {suffix}"

    def create_mapper_obj(self):
        self.mapper = Mapper.objects.create()

    def create_external_links_obj(self):
        self.external_links = ExternalLinks.objects.create()

    def save(self, *args, **kwargs):
        slug_str = "%s %s %s" % (
            self.PROFILE_TYPE,
            self.name,
            self.club.name if self.club else "",
        )
        unique_slugify(self, slug_str)

        if not self.mapper:
            self.create_mapper_obj()

        if not self.external_links:
            self.create_external_links_obj()

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Team")
        verbose_name_plural = _("Teams")
        unique_together = ("name", "club", "seniority", "league")

    # common team fileds
    travel_refunds = models.BooleanField(_("Zwrot za dojazdy"), default=False)

    game_bonus = models.BooleanField(
        _("Premie za mecze"),
        default=False,
    )

    scolarships = models.BooleanField(
        _("Stypendia"),
        default=False,
    )

    gloves_shoes_refunds = models.BooleanField(
        _("Zwroty za buty/rękawice"),
        default=False,
    )

    traning_gear = models.BooleanField(
        _("Sprzęt treningowy"),
        default=False,
    )

    regular_gear = models.BooleanField(
        _("Sprzęt wyjściowy"),
        default=False,
    )

    secondary_trainer = models.BooleanField(
        _("Drugi trener"),
        default=False,
    )

    fizo = models.BooleanField(
        _("Fizjoterapeuta"),
        default=False,
    )

    diet_suplements = models.BooleanField(
        _("Suplemnety / odżywki"),
        default=False,
    )

    def __str__(self):
        return self.team_name_with_current_league


class TeamHistory(models.Model):
    """Definition of a  team history object

    Keeps track of a team history in a past
    """

    team = models.ForeignKey(
        "Team", on_delete=models.CASCADE, related_name="historical"
    )
    season = models.ForeignKey(
        "Season",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="The season associated with this team history entry.",
    )
    coach = models.ForeignKey(
        "profiles.CoachProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coached_team_histories",
        help_text="The coach who led the team during this season.",
    )

    data_mapper_id = models.PositiveIntegerField(
        help_text="ID of object placed in data_ database. It should alwayes reflect scheme which represents.",
        blank=True,
        null=True,
    )

    team_name_raw = models.CharField(
        max_length=250, blank=True, null=True, help_text="Team name from scrapper."
    )

    league_history = models.ForeignKey(
        "LeagueHistory",
        on_delete=models.SET_NULL,
        related_name="league_history",
        null=True,
        blank=True,
    )

    mapper = models.OneToOneField(
        Mapper, on_delete=models.SET_NULL, blank=True, null=True
    )

    visible = models.BooleanField(default=True)

    data = models.JSONField(null=True, blank=True)
    autocreated = models.BooleanField(default=False, help_text="Autocreated")

    def __str__(self):
        return self.team.name_with_league_full

    def create_mapper_obj(self):
        self.mapper = Mapper.objects.create()

    def save(self, *args, **kwargs):
        if not self.mapper:
            self.create_mapper_obj()
        super().save()

    class Meta:
        unique_together = ("mapper", "league_history")


class JuniorAgeGroup(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class TeamManagers(models.Model):
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="managers",
        help_text="Reference to the team with which this manager is associated. A team can have multiple managers.",
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="manager_teams",
        help_text="Reference to the user profile managing the team",
    )
