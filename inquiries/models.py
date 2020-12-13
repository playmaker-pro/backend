from django.db import models
from django.utils.translation import gettext_lazy as _
# Create your models here.
from django.conf import settings
from django_fsm import FSMField, transition
from notifications.mail import request_new, request_accepted, request_declined
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


class RequestType(models.Model):  # @todo not tested 
    name = models.CharField(max_length=240)


class InquiryRequestQuerySet(models.QuerySet):
    def resolved(self):
        return self.filter(status=self.model.RESOLVED_STATES)

    def active(self):
        return self.filter(status=self.model.ACTIVE_STATES)


class InquiryRequestManager(models.Manager):  # @todo not tested 
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

    body = models.TextField(null=True, blank=True)

    status = FSMField(
        default=STATUS_NEW,
        choices=STATUS_CHOICES,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

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

    def is_active(self):
        return self.status in self.ACTIVE_STATES

    def is_resolved(self):
        return self.status in self.RESOLVED_STATES

    @transition(field=status, source=[STATUS_NEW], target=STATUS_SENT)
    def send(self):
        '''Should be appeared when message was distributed to recipient'''
        request_new(self)

    @transition(field=status, source=[STATUS_SENT], target=STATUS_RECEIVED)
    def read(self):
        '''Should be appeared when message readed/seen by recipient'''

    @transition(field=status, source=[STATUS_NEW, STATUS_SENT], target=STATUS_ACCEPTED)
    def accept(self):
        '''Should be appeared when message was accepted by recipient'''
        request_accepted(self)

    @transition(field=status, source=[STATUS_NEW, STATUS_SENT], target=STATUS_REJECTED)
    def reject(self):
        '''Should be appeared when message was rejected by recipient'''
        request_declined(self)

    def __str__(self):
        return f'{self.sender} --({self.status})-> {self.recipient}'

    def save(self, *args, **kwargs):
        self.body = ContactBodySnippet.generate(self.sender)
        if self.status == self.STATUS_NEW:
            self.send()
        super().save(*args, **kwargs)


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
