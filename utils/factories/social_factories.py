import factory
from allauth.socialaccount.models import SocialAccount, SocialApp


class SocialAccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SocialAccount

    user = 1
    provider = "google"
    uid = "1234"
    extra_data = {"sub": "1234"}


class SocialAppFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SocialApp

    provider = "google"
    name = "google"
    client_id = "client_id"
    secret = "secret"
    key = "key"
