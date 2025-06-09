from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

from profiles.models import BaseProfile, PlayerPosition, TeamContributor
from roles import definitions


class TransferBaseModel(models.Model):
    """Transfer base model."""

    salary = models.CharField(
        max_length=10,
        default=None,
        null=True,
        blank=True,
        choices=definitions.TRANSFER_SALARY_CHOICES,
        help_text="Define salary",
    )
    benefits = ArrayField(
        models.CharField(
            max_length=255,
            null=True,
            blank=True,
            choices=definitions.TRANSFER_BENEFITS_CHOICES,
            help_text="Additional information about the transfer.",
        ),
        null=True,
        blank=True,
        help_text=_("Benefits defines as integers with comma. Example: 1,2"),
    )
    number_of_trainings = models.CharField(
        max_length=10,
        default=None,
        null=True,
        blank=True,
        choices=definitions.TRANSFER_TRAININGS_CHOICES,
        help_text="Define number of trainings per week",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ProfileTransferStatus(TransferBaseModel):
    """Keeps track on profile transfer status"""

    meta = models.ForeignKey(
        "profiles.ProfileMeta",
        on_delete=models.CASCADE,
        related_name="transfer_status",
        help_text="The profile meta that this transfer status belongs to.",
    )
    status = models.CharField(
        max_length=255,
        choices=definitions.TRANSFER_STATUS_CHOICES,
        help_text="Defines a status of the transfer for the profile.",
    )
    league = models.ManyToManyField(
        "clubs.League",
        related_name="transfer_status",
    )
    additional_info = ArrayField(
        models.CharField(
            max_length=10,
            choices=definitions.TRANSFER_STATUS_ADDITIONAL_INFO_CHOICES,
            help_text="Additional information about the transfer.",
        ),
        null=True,
    )

    @property
    def profile(self) -> BaseProfile:
        """Returns the user profile."""
        return self.meta.profile


class ProfileTransferRequest(TransferBaseModel):
    """
    Represents a profile transfer request in the context of profile needs
    (for example soccer clubs and coaches).

    This model tracks transfer requests initiated by profiles
    (coaches or club representatives) to request players for team participation.
    """

    meta = models.ForeignKey(
        "profiles.ProfileMeta",
        on_delete=models.CASCADE,
        related_name="transfer_requests",
        help_text="The profile meta that this transfer request belongs to.",
    )

    requesting_team = models.ForeignKey(
        TeamContributor,
        on_delete=models.CASCADE,
        related_name="transfer_requests",
        help_text="The team that is requesting the transfer.",
    )
    gender = models.CharField(
        max_length=10, choices=(("M", "M"), ("F", "F")), help_text="Define team gender"
    )

    status = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=definitions.TRANSFER_REQUEST_STATUS_CHOICES,
        help_text="Defines a status of the transfer for the profile.",
    )
    position = models.ManyToManyField(
        PlayerPosition,
        related_name="transfer_requests",
        help_text="The position that the team is requesting.",
    )
    league = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text=_("League name filled automatically from team.club.voivodeship_obj"),
    )
    voivodeship = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text=_(
            "Voivodeship name filled automatically from team.club.voivodeship_obj"
        ),
    )

    def save(self, *args, **kwargs):
        """
        Override save method to fill league and voivodeship fields. Fields are needed
        for filtering transfer requests in the transfer request search.
        """
        if self.team and self.team.league:
            self.league = self.team.league.name
        club = self.team.club if self.team else None
        if club and club.voivodeship_obj:
            self.voivodeship = club.voivodeship_obj.name
        return super().save(*args, **kwargs)

    @property
    def profile(self) -> BaseProfile:
        """Returns the user profile."""
        return self.meta.profile

    @property
    def team(self):
        """Returns the requesting team."""
        return self.requesting_team.team_history.first()
