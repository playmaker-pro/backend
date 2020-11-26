import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.urls import reverse


class Club(models.Model):
    editors = models.ManyToManyField(
        settings.AUTH_USER_MODEL)

    picture = models.ImageField(
        _("Zdjęcie"),
        upload_to="club_pics/%Y-%m-%d/",
        null=True,
        blank=True)

    data_mapper_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='ID of object placed in data_ database. It should alwayes reflect scheme which represents.')

    slug = models.UUIDField(
       default=uuid.uuid4,
       blank=True,
       editable=False)

    name = models.CharField(
        _('Club name'),
        max_length=255,
        help_text='Displayed Name of club')

    def get_permalink(self):
        return reverse("clubs:show_club", kwargs={"slug": self.slug})

    class Meta:
        verbose_name = _('Klub')
        verbose_name_plural = _('Kluby')

    def __str__(self):
        return f'{self.name}# '


class Team(models.Model):
    # editors = models.OneToOneField(
    #     settings.AUTH_USER_MODEL)

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

    slug = models.UUIDField(
       default=uuid.uuid4,
       blank=True,
       editable=False)

    name = models.CharField(
        _('Team name'),
        max_length=255,
        help_text='Displayed Name of team')

    def get_permalink(self):
        return reverse("clubs:show_team", kwargs={"slug": self.slug})

    class Meta:
        verbose_name = _('Team')
        verbose_name_plural = _("Teams")

    def __str__(self):
        return f'{self.club.name}:{self.name}'
