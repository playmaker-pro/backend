import factory

from mailing.models import Mailing


class MailingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Mailing
        django_get_or_create = ("user",)
