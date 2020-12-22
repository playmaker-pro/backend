from django.db import models
from django.utils.translation import gettext_lazy as _
# Create your models here.
from django.conf import settings
from django_fsm import FSMField, transition
from notifications.mail import request_new, request_accepted, request_declined
# This can be extracted to models.User.
from django_countries.fields import CountryField
# class DefaultPlan(models.Model):
#     # role_type = models.
#     user_type = models.CharField()
#     plan = models.OneToOneField(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         primary_key=True)
from address.models import AddressField

from profiles.models import PlayerPosition


class AnnouncementPlan(models.Model):
    '''Holds information about user's annoucment plans.
    '''
    name = models.CharField(
        _('Plan Name'),
        max_length=255,
        help_text=_('Plan name'))

    limit = models.PositiveIntegerField(
        _('Plan limit'),
        help_text=_('Limit how many actions are allowed'))

    sort = models.PositiveIntegerField(
        ('Soring'),
        default=0,
        help_text=_('Used to sort plans low numbers threaded as lowest plans. Default=0 which means this is not set.'))

    description = models.TextField(
        _('Description'),
        null=True,
        blank=True,
        help_text=_('Short description what is rationale behind plan. Used only for internal purpose.'))

    default = models.BooleanField(
        _('Default Plan'),
        default=False,
        help_text=_('Defines if this is default plan selected during account creation.'))

    class Meta:
        unique_together = ('name', 'limit')

    def __str__(self):
        return f'{self.name}({self.limit})'


class AnnouncementUserQuota(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True)

    plan = models.ForeignKey(
        AnnouncementPlan,
        on_delete=models.CASCADE
    )

    counter = models.PositiveIntegerField(
        _('Obecna ilość ogłoszeń'),
        default=0,
        help_text=_('Current number of used inquiries.'))

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
        '''Reset current counter'''
        self.counter = 0
        self.save()

    def increment(self):
        '''Increase by one counter'''
        self.counter += 1
        self.save()

    def __str__(self):
        return f'{self.user}: {self.counter}/{self.plan.limit}'


from clubs.models import League, Voivodeship, Seniority, Gender, Club


class Announcement(models.Model):
    STATUS_NEW = 'NOWE'
    STATUS_SENT = 'WYSŁANO'
    STATUS_RECEIVED = 'PRZECZYTANE'
    # STATUS_READED = 'READED'
    STATUS_ACCEPTED = 'ZAAKCEPTOWANE'
    STATUS_REJECTED = 'ODRZUCONE'

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

    # state = InquiryRequestManager()

    status = FSMField(
        default=STATUS_NEW,
        choices=STATUS_CHOICES,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    positions = models.ManyToManyField(PlayerPosition)

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='announcement_creator',
        on_delete=models.CASCADE
    )
    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE
    )

    country = CountryField(
        _('Country'),
        # blank=True,
        default='PL',
        null=True,
        blank_label=_('Wybierz kraj'),
    )

    league = models.ForeignKey(
        League,
        on_delete=models.CASCADE
    )

    seniority = models.ForeignKey(
        Seniority,
        on_delete=models.CASCADE
    )

    gender = models.ForeignKey(
        Gender,
        on_delete=models.CASCADE
    )

    voivodeship = models.ForeignKey(
        Voivodeship,
        on_delete=models.CASCADE
    )

    body = models.TextField()

    www = models.URLField(null=True, blank=True)

    address = AddressField(
        help_text=_('Adres'),
        blank=True,
        null=True)
