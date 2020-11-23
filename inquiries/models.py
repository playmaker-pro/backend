from django.db import models
from django.utils.translation import gettext_lazy as _
# Create your models here.
from django.conf import settings
from django_fsm import FSMField, transition

# This can be extracted to models.User.

# class DefaultPlan(models.Model):
#     # role_type = models.
#     user_type = models.CharField()
#     plan = models.OneToOneField(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         primary_key=True)


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


class InquiryRequest(models.Model):
    STATUS_NEW = 'NEW'
    STATUS_SENT = 'SENT'
    STATUS_RECEIVED = 'RECEIVED'
    # STATUS_READED = 'READED'
    STATUS_ACCEPTED = 'ACCEPTED'
    STATUS_REJECTED = 'REJECTED'

    STATUS_CHOICES = (
        (STATUS_NEW, STATUS_NEW),
        (STATUS_SENT, STATUS_SENT),
        (STATUS_RECEIVED, STATUS_RECEIVED),
        # (STATUS_READED, STATUS_READED),
        (STATUS_ACCEPTED, STATUS_ACCEPTED),
        (STATUS_REJECTED, STATUS_REJECTED),
    )

    status = FSMField(
        default=STATUS_NEW
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='sender_request_recipient',
        on_delete=models.CASCADE
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='inquiry_request_recipient',
        on_delete=models.CASCADE
    )

    @transition(field=status, source=[STATUS_NEW], target=STATUS_SENT)
    def send(self):
        '''Should be appeared when message was distributed to recipient'''

    @transition(field=status, source=[STATUS_SENT], target=STATUS_RECEIVED)
    def read(self):
        '''Should be appeared when message readed/seen by recipient'''

    @transition(field=status, source=[STATUS_NEW, STATUS_SENT], target=STATUS_ACCEPTED)
    def accept(self):
        '''Should be appeared when message was accepted by recipient'''

    @transition(field=status, source=[STATUS_NEW, STATUS_SENT], target=STATUS_REJECTED)
    def reject(self):
        '''Should be appeared when message was rejected by recipient'''

    def __str__(self):
        return f'{self.sender} --({self.status})-> {self.recipient}'
