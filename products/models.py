from django.db import models
from django.utils.translation import gettext_lazy as _
# Create your models here.
from django.conf import settings
from django_fsm import FSMField, transition
from notifications.mail import request_new, request_accepted, request_declined
# This can be extracted to models.User.
from django_countries.fields import CountryField
from django.utils import timezone
from address.models import AddressField

from profiles.models import PlayerPosition

from clubs.models import League, Voivodeship, Seniority, Gender, Club
from datetime import timedelta

from .notifications import ProductMail


class PageDescription(models.Model):    
    text = models.TextField()


class Product(models.Model):
    title = models.CharField(max_length=455, null=True, blank=True)
    subtitle = models.CharField(max_length=455, null=True, blank=True)
    place = models.CharField(max_length=455, null=True, blank=True)
    person = models.CharField(max_length=455, null=True, blank=True)
    teaser = models.CharField(max_length=455, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=False)
    html_body = models.TextField(null=True, blank=True)
    html_form = models.TextField(null=True, blank=True)
    tags = models.ManyToManyField('Tag')

    def __unicode__(self):
        return f'{self.title}'


class Tag(models.Model):
    name = models.CharField(max_length=200)
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return f'{self.name}'


class UserRequest(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True)

    date = models.DateTimeField(auto_created=True, auto_now=True)

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )
    raw_body = models.JSONField(null=True, blank=True)
  
    class Meta:
        unique_together = ('user', 'product', 'date')

    @property
    def body_pretty(self):
        return self.raw_body

    def __unicode__(self):
        return f'{self.user} {self.product}'

    def send_notifcation_to_user(self):
        ProductMail.mail_user_about_his_request(self)

    def send_notification_to_admin(self):
        ProductMail.mail_admins_about_new_product_request(self)

