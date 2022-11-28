from django.db import models
from django.conf import settings
from clubs.models import Team, Club
from django.utils.translation import gettext_lazy as _
from django.forms.models import model_to_dict
from datetime import datetime
from utils import make_choices
from clubs.models import League


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)

    @property
    def display_role(self):
        return self.name

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = "Rola"
        verbose_name_plural = "Role"

class LeadStatus(models.Model):

    FOLLOWED_FIELDS = [
        "id",
        "user",
        "club",
        "team",
        "first_name",
        "last_name",
        "phone",
        "email",
        "facebook_url",
        "twitter_url",
        "linkedin_url",
        "instagram_url",
        "website_url",
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lead",
    )
    user_role = models.ForeignKey(
        Role, null=True, blank=True, related_name="lead_role", on_delete=models.SET_NULL
    )
    club = models.ForeignKey(
        Club,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lead_club",
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lead_team",
    )
    first_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    last_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    phone = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    email = models.EmailField(null=True, blank=True)
    facebook_url = models.URLField(_("Facebook"), max_length=500, blank=True, null=True)
    twitter_url = models.URLField(_("Twitter"), max_length=500, blank=True, null=True)
    linkedin_url = models.URLField(_("Linkedin"), max_length=500, blank=True, null=True)
    instagram_url = models.URLField(
        _("Instagram"), max_length=500, blank=True, null=True
    )
    website_url = models.URLField(_("Website"), max_length=500, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lead_creator",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lead_updater",
    )
    data_mapper_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="ID of object placed in data_ database. It should alwayes reflect scheme which represents.",
    )
    is_actual = models.BooleanField(default=True)
    previous = models.OneToOneField(
        "self", on_delete=models.SET_NULL, blank=True, null=True, related_name="next"
    )

    @property
    def full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}"

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._loaded_values = dict(zip(instance.FOLLOWED_FIELDS, values))
        return instance

    def save(self, *args, **kwargs):
        if not self._state.adding:
            cleaned_data = model_to_dict(self, fields=self.FOLLOWED_FIELDS)
            data_changed = self.is_model_changed(cleaned_data)
            if data_changed:
                LeadStatus.objects.create(
                    **self.parse_input(cleaned_data),
                    created_by=self.updated_by,
                    date_created=datetime.now(),
                    previous=self,
                )
                self.is_actual = False
                self.date_updated = datetime.now()
                kwargs["update_fields"] = ["is_actual", "date_updated", "updated_by"]
        super().save(*args, **kwargs)

    def parse_input(self, data_input):
        data_input.pop("id")
        data_input["user_id"] = data_input.pop("user")
        data_input["club_id"] = data_input.pop("club")
        data_input["team_id"] = data_input.pop("team")
        return data_input

    def is_model_changed(self, post_data):
        return self._loaded_values != post_data

    class Meta:
        ordering = ["-is_actual"]
        verbose_name = "Kontakt"
        verbose_name_plural = "Kontakty"

    def __str__(self):
        return str(
            self.full_name
            if self.first_name and self.last_name
            else self.user or self.team or self.club
        )


class ContactPurpose(models.Model):
    name = models.CharField(max_length=150, unique=True)

    @property
    def display_purpose(self):
        return self.name

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = "Cel"
        verbose_name_plural = "Cele rozmów"


class Conversation(models.Model):

    CONTACT_METHODS = (
        ("Phone call", "Phone call"),
        ("Live", "Live"),
        ("Mail", "Mail"),
        ("Twitter", "Twitter"),
        ("Facebook", "Facebook"),
        ("LinkedIn", "LinkedIn"),
        ("Instagram", "Instagram"),
        ("Website", "Website"),
    )

    lead = models.ForeignKey(
        LeadStatus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lead",
    )
    contact_method = models.CharField(
        max_length=20,
        choices=CONTACT_METHODS,
        null=True,
        blank=True,
    )
    contact_purpose = models.ForeignKey(
        ContactPurpose,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contact_method",
    )
    note = models.TextField(null=True, blank=True)
    todo = models.TextField(null=True, blank=True)
    by_who = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="responsible_user",
        verbose_name="Responsible user",
    )
    is_done = models.BooleanField(default=False)
    reminding_contact = models.DateTimeField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="created_by",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="updated_by",
    )
    financial_conditions_from = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    financial_conditions_to = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    city = models.CharField(_("Miasto"), max_length=200, blank=True, null=True)
    range = models.PositiveIntegerField(
        _("Promień odległości w kilometrach"), null=True, blank=True
    )

    class Meta:
        verbose_name = "Rozmowe"
        verbose_name_plural = "Rozmowy"


class Demand(models.Model):
    POSITION_CHOICES = [
        (1, "Bramkarz"),
        (2, "Obrońca Lewy"),
        (3, "Obrońca Prawy"),
        (4, "Obrońca Środkowy"),
        (5, "Pomocnik defensywny"),
        (6, "Pomocnik środkowy"),
        (7, "Pomocnik ofensywny"),
        (8, "Skrzydłowy"),
        (9, "Napastnik"),
    ]

    conversation = models.ForeignKey(
        Conversation,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    position = models.IntegerField(
        _("Pozycja"),
        choices=make_choices(POSITION_CHOICES),
        blank=True,
        null=True,
    )
    league = models.ManyToManyField(
        League, null=True, blank=True, verbose_name="Poziom rozgrywkowy"
    )
    is_junior = models.BooleanField(
        _("Młodzieżówka"),
        default=False,
    )

    class Meta:
        verbose_name = "Zapotrzebowanie"
        verbose_name_plural = "Zapotrzebowanie"

