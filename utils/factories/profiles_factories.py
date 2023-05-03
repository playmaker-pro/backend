import factory
from django.contrib.auth import get_user_model

from profiles.models import PlayerMetrics, PlayerProfile
from utils.factories.mapper_factories import MapperFactory

user = get_user_model()
_USER_EMAIL = "unittest@playmaker.pro"


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = user
        django_get_or_create = ("email",)

    email = _USER_EMAIL


class PlayerProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlayerProfile
        django_get_or_create = ("user",)

    user = factory.SubFactory(UserFactory)
    mapper = factory.SubFactory(MapperFactory)


class PlayerMetricsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlayerMetrics

    def __init__(self, player: PlayerProfile):
        self.player = player

    player = factory.SubFactory(PlayerProfileFactory)
