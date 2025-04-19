from datetime import timedelta

from address.models import AddressField

# Create your models here.
from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# This can be extracted to models.User.
from django_countries.fields import CountryField
from django_fsm import FSMField

from clubs.models import Club, Gender, League, Seniority, Voivodeship
from profiles.models import PlayerPosition
from voivodeships.models import Voivodeships

LICENCE_CHOICES = (
    (1, "UEFA PRO"),
    (2, "UEFA A"),
    (3, "UEFA EY A"),
    (4, "UEFA B"),
    (5, "UEFA C"),
    (6, "GRASS C"),
    (7, "GRASS D"),
    (8, "UEFA Futsal B"),
    (9, "PZPN A"),
    (10, "PZPN B"),
    (11, "W trakcie kursu"),
)


def get_licence_choice_number(licence_name: str) -> int:
    for licence_pair in LICENCE_CHOICES:
        if licence_pair[1] == licence_name:
            return licence_pair[0]
    return 0


class AnnouncementPlan(models.Model):
    """
    Holds information about user's announcement plans.
    """

    name = models.CharField(_("Plan Name"), max_length=255, help_text=_("Plan name"))

    limit = models.PositiveIntegerField(
        _("Plan limit"), help_text=_("Limit how many actions are allowed")
    )

    days = models.DurationField(
        default=timedelta,
        null=True,
        blank=True,
        help_text=_(
            "Number of days to set after which plan expires. Can be null which means is not activated."
        ),
    )

    sort = models.PositiveIntegerField(
        ("Soring"),
        default=0,
        help_text=_(
            "Used to sort plans low numbers threaded as lowest plans. Default=0 which means this is not set."
        ),
    )

    description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
        help_text=_(
            "Short description what is rationale behind plan. Used only for internal purpose."
        ),
    )

    default = models.BooleanField(
        _("Default Plan"),
        default=False,
        help_text=_(
            "Defines if this is default plan selected during account creation."
        ),
    )

    class Meta:
        unique_together = ("name", "limit")

    def __str__(self):
        return f"{self.name}({self.limit})"


class AnnouncementUserQuota(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True
    )

    plan = models.ForeignKey(AnnouncementPlan, on_delete=models.CASCADE)

    counter = models.PositiveIntegerField(
        _("Obecna ilość ogłoszeń"),
        default=0,
        help_text=_("Current number of used inquiries."),
    )

    @property
    def can_make_request(self):
        return self.limit >= self.counter

    @property
    def left(self):
        return self.plan.limit - self.counter

    @property
    def limit(self):
        return self.plan.limit

    def reset(self):
        """Reset current counter"""
        self.counter = 0
        self.save()

    def increment(self):
        """Increase by one counter"""
        self.counter += 1
        self.save()

    def __str__(self):
        return f"{self.user}: {self.plan.name}({self.counter}/{self.plan.limit})"


class ActiveAnnouncementManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                status__in=AnnouncementMeta.ACTIVE_STATES,
            )
        )


class AnnouncementMeta(models.Model):
    active = ActiveAnnouncementManager()
    objects = models.Manager()

    STATUS_NEW = "NOWE"
    STATUS_SENT = "WYSŁANO"
    STATUS_RECEIVED = "PRZECZYTANE"
    # STATUS_READED = 'READED'
    STATUS_ACCEPTED = "ZAAKCEPTOWANE"
    STATUS_REJECTED = "ODRZUCONE"

    ACTIVE_STATES = [STATUS_NEW, STATUS_SENT, STATUS_RECEIVED]
    RESOLVED_STATES = [STATUS_ACCEPTED, STATUS_REJECTED]

    STATUS_CHOICES = (
        (STATUS_NEW, STATUS_NEW),
        (STATUS_SENT, STATUS_SENT),
        (STATUS_RECEIVED, STATUS_RECEIVED),
        # (STATUS_READED, STATUS_READED),
        (STATUS_ACCEPTED, STATUS_ACCEPTED),
        (STATUS_REJECTED, STATUS_REJECTED),
    )

    status = FSMField(
        default=STATUS_NEW,
        choices=STATUS_CHOICES,
    )

    disabled = models.BooleanField(default=False)

    expire = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    subscribers = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)

    def set_expiration_date(self):
        if self.expire is None:
            self.expire = timezone.now() + self.creator.announcementuserquota.plan.days

    def save(self, *args, **kwargs):
        self.set_expiration_date()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.creator} #nr {self.id}"

    class Meta:
        abstract = True


class ClubForPlayerAnnouncement(AnnouncementMeta):
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="announcement_creator",
        on_delete=models.CASCADE,
    )
    positions = models.ManyToManyField(PlayerPosition)

    club = models.ForeignKey(Club, on_delete=models.CASCADE)

    country = CountryField(
        _("Country"),
        # blank=True,
        default="PL",
        null=True,
        blank_label=_("Wybierz kraj"),
    )

    year_from = models.PositiveIntegerField(
        help_text=_("Rocznik piłkarza od.. np. 1986"),
    )

    year_to = models.PositiveIntegerField(
        help_text=_("Rocznik piłkarza ..do np. 1986"),
    )

    league = models.ForeignKey(League, on_delete=models.CASCADE, null=True, blank=True)

    seniority = models.ForeignKey(
        Seniority, on_delete=models.CASCADE, null=True, blank=True
    )

    gender = models.ForeignKey(Gender, on_delete=models.CASCADE, null=True, blank=True)

    # TODO Based on task PM-363. After migration on production, field can be deleted
    voivodeship = models.ForeignKey(
        Voivodeship,
        on_delete=models.CASCADE,
        verbose_name=_("Województwo"),
        help_text="Wybierz województwo. Stare pole, gotowe do migracji",
        null=True,
        blank=True,
    )
    voivodeship_obj = models.ForeignKey(
        Voivodeships,
        on_delete=models.SET_NULL,
        verbose_name=_("Województwo"),
        help_text="Wybierz województwo. Nowe pole",
        null=True,
        blank=True,
    )

    body = models.TextField()

    www = models.URLField(null=True, blank=True)

    address = AddressField(help_text=_("Adres"), blank=True, null=True)


class PlayerForClubAnnouncement(AnnouncementMeta):
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="player_for_club_announcement_creator",
        on_delete=models.CASCADE,
    )
    position = models.ForeignKey(PlayerPosition, on_delete=models.CASCADE)

    # TODO Based on task PM-363. After migration on production, field can be deleted
    voivodeship = models.ForeignKey(
        Voivodeship,
        on_delete=models.CASCADE,
        verbose_name=_("Województwo"),
        help_text="Wybierz województwo. Stare pole, gotowe do migracji",
        null=True,
        blank=True,
    )
    voivodeship_obj = models.ForeignKey(
        Voivodeships,
        on_delete=models.SET_NULL,
        verbose_name=_("Województwo"),
        help_text="Wybierz województwo. Nowe pole",
        null=True,
        blank=True,
    )

    address = AddressField(help_text=_("Adres"), blank=True, null=True)

    practice_distance = models.CharField(max_length=3)

    league = models.ForeignKey(
        League,
        on_delete=models.CASCADE,
        related_name="player_for_club_announcement_league",
        null=True,
    )

    target_league = models.ForeignKey(
        League,
        on_delete=models.CASCADE,
    )

    body = models.TextField()


class ClubForCoachAnnouncement(AnnouncementMeta):
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="club_for_coach_announcement_creator",
        on_delete=models.CASCADE,
    )

    club = models.ForeignKey(Club, on_delete=models.CASCADE)

    league = models.ForeignKey(
        League,
        on_delete=models.CASCADE,
        related_name="club_for_coach_announcement_league",
    )

    # TODO Based on task PM-363. After migration on production, field can be deleted
    voivodeship = models.ForeignKey(
        Voivodeship,
        on_delete=models.CASCADE,
        verbose_name=_("Województwo"),
        help_text="Wybierz województwo. Stare pole, gotowe do migracji",
        null=True,
        blank=True,
    )
    voivodeship_obj = models.ForeignKey(
        Voivodeships,
        on_delete=models.SET_NULL,
        verbose_name=_("Województwo"),
        help_text="Wybierz województwo. Nowe pole",
        null=True,
        blank=True,
    )

    lic_type = models.IntegerField(
        _("Licencja"), choices=LICENCE_CHOICES, blank=True, null=True
    )

    seniority = models.ForeignKey(Seniority, on_delete=models.CASCADE)

    gender = models.ForeignKey(Gender, on_delete=models.CASCADE)

    body = models.TextField()

    def get_licence_name(self) -> str:
        return LICENCE_CHOICES[self.lic_type - 1][1]


class CoachForClubAnnouncement(AnnouncementMeta):
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="coach_for_club_announcement_creator",
        on_delete=models.CASCADE,
    )

    lic_type = models.IntegerField(
        _("Licencja"), choices=LICENCE_CHOICES, blank=True, null=True
    )

    # TODO Based on task PM-363. After migration on production, field can be deleted
    voivodeship = models.ForeignKey(
        Voivodeship,
        on_delete=models.CASCADE,
        verbose_name=_("Województwo"),
        help_text="Wybierz województwo. Stare pole, gotowe do migracji",
        null=True,
        blank=True,
    )
    voivodeship_obj = models.ForeignKey(
        Voivodeships,
        on_delete=models.SET_NULL,
        verbose_name=_("Województwo"),
        help_text="Wybierz województwo. Nowe pole",
        null=True,
        blank=True,
    )

    address = AddressField(help_text=_("Adres"), blank=True, null=True)

    practice_distance = models.CharField(
        max_length=3, validators=[RegexValidator(r"^\d{1,3}$")]
    )

    league = models.ForeignKey(
        League,
        on_delete=models.CASCADE,
        related_name="coach_for_club_announcement_league",
        null=True,
    )

    target_league = models.ForeignKey(
        League,
        on_delete=models.CASCADE,
    )

    body = models.TextField()

    def get_licence_name(self) -> str:
        return LICENCE_CHOICES[self.lic_type - 1][1]
