import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Club(models.Model):
    editors = models.ManyToManyField(
        settings.AUTH_USER_MODEL)

    slug = models.UUIDField(
       default=uuid.uuid4,
       blank=True,
       editable=False)

    name = models.CharField(
        _('Club name'),
        max_length=255,
        help_text='Displayed Name of club')

    class Meta:
        verbose_name = _('Club')
        verbose_name_plural = _('Clubs')

    def __str__(self):
        return f'{self.name}# '


class Team(models.Model):
    club = models.ForeignKey(
        Club,
        related_name='teams',
        null=True,
        on_delete=models.SET_NULL,
    )

    name = models.CharField(
        _('Team name'),
        max_length=255,
        help_text='Displayed Name of club')

    class Meta:
        verbose_name = _('Team')
        verbose_name_plural = _("Teams")

    def __str__(self):
        return f'{self.club.name}:{self.name}'
