import logging

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition
from notifications.mail import request_accepted, request_declined, request_new

logger = logging.getLogger(__name__)


class InquiryPlan(models.Model):
    '''Holds information about user's inquiry plans.
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


class UserInquiry(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True)

    plan = models.ForeignKey(
        InquiryPlan,
        on_delete=models.CASCADE
    )

    counter = models.PositiveIntegerField(
        _('Obecna ilość zapytań'),
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


class RequestType(models.Model):
    name = models.CharField(max_length=240)


class InquiryRequestQuerySet(models.QuerySet):
    def resolved(self):
        return self.filter(status=self.model.RESOLVED_STATES)

    def active(self):
        return self.filter(status=self.model.ACTIVE_STATES)


class InquiryRequestManager(models.Manager):
    def get_queryset(self):
        return InquiryRequestQuerySet(self.model, using=self._db)

    def resolved(self):
        return self.get_queryset().resolved()

    def active(self):
        return self.get_queryset().active()


class InquiryRequest(models.Model):
    STATUS_NEW = 'NOWE'
    STATUS_SENT = 'WYSŁANO'
    STATUS_RECEIVED = 'PRZECZYTANE'
    STATUS_ACCEPTED = 'ZAAKCEPTOWANE'
    STATUS_REJECTED = 'ODRZUCONE'
    UNSEEN_STATES = [STATUS_SENT]
    ACTIVE_STATES = [STATUS_NEW, STATUS_SENT, STATUS_RECEIVED]
    RESOLVED_STATES = [STATUS_ACCEPTED, STATUS_REJECTED]

    CATEGORY_CLUB = 'club'
    CATEGORY_TEAM = 'team'
    CATEGORY_USER = 'user'

    CATEGORY_CHOICES = (
        (CATEGORY_USER, CATEGORY_USER),
        (CATEGORY_TEAM, CATEGORY_TEAM),
        (CATEGORY_CLUB, CATEGORY_CLUB),
    )

    STATUS_CHOICES = (
        (STATUS_NEW, STATUS_NEW),
        (STATUS_SENT, STATUS_SENT),
        (STATUS_RECEIVED, STATUS_RECEIVED),
        (STATUS_ACCEPTED, STATUS_ACCEPTED),
        (STATUS_REJECTED, STATUS_REJECTED),
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    # content = models.JSONField(null=True, blank=True)

    body = models.TextField(null=True, blank=True)

    body_recipient = models.TextField(null=True, blank=True)

    status = FSMField(
        default=STATUS_NEW,
        choices=STATUS_CHOICES)

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='sender_request_recipient',
        on_delete=models.CASCADE)

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='inquiry_request_recipient',
        on_delete=models.CASCADE)

    category = models.CharField(
        default=CATEGORY_USER,
        choices=CATEGORY_CHOICES,
        max_length=255)

    @property
    def is_user_type(self):
        return self.category == self.CATEGORY_USER

    @property
    def is_club_type(self):
        return self.category == self.CATEGORY_CLUB

    @property
    def is_team_type(self):
        return self.category == self.CATEGORY_TEAM

    def is_active(self):
        return self.status in self.ACTIVE_STATES

    def is_resolved(self):
        return self.status in self.RESOLVED_STATES

    def status_display_for(self, user):
        status_map = {}
        if user == self.recipient:
            status_map = {
                'WYSŁANO': 'OTRZYMANO'
            }
        return status_map.get(self.status, self.status)

    @transition(field=status, source=[STATUS_NEW], target=STATUS_SENT)
    def send(self):
        '''Should be appeared when message was distributed to recipient'''
        request_new(self)

    @transition(field=status, source=[STATUS_SENT], target=STATUS_RECEIVED)
    def read(self):
        '''Should be appeared when message readed/seen by recipient'''

    @transition(field=status, source=[STATUS_NEW, STATUS_SENT, STATUS_RECEIVED], target=STATUS_ACCEPTED)
    def accept(self):
        '''Should be appeared when message was accepted by recipient'''
        logger.debug(f'#{self.pk} reuqest accepted creating sender and recipient contanct body')
        self.body = ContactBodySnippet.generate(self.sender)
        self.body_recipient = ContactBodySnippet.generate(self.recipient)
        request_accepted(self)

    @transition(field=status, source=[STATUS_NEW, STATUS_SENT, STATUS_RECEIVED], target=STATUS_REJECTED)
    def reject(self):
        '''Should be appeared when message was rejected by recipient'''
        request_declined(self)

    def save(self, *args, **kwargs):
        if self.status == self.STATUS_NEW:
            self.send()  # @todo due to problem with detecting changes of paramters here is hax to alter status to send, durgin which message is sedn via mail
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.sender} --({self.status})-> {self.recipient}'


class ContactBodySnippet:
    @classmethod
    def generate(cls, user):

        body = ''
        if user.profile.phone:
            body += f'{user.profile.phone} / \n'

        body += f'{user.email}\n'
        # if user.profile.facebook_url:
        #     body += f'FB: {user.profile.facebook_url}\n'
        return body
