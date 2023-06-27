import factory
from django.contrib.auth import get_user_model
from .user_factories import UserFactory
from profiles.models import PlayerMetrics, PlayerProfile
from utils.factories.mapper_factories import MapperFactory

User = get_user_model()


class PlayerProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlayerProfile
        django_get_or_create = ("user",)

    user = factory.SubFactory(UserFactory)
    mapper = factory.SubFactory(MapperFactory)


class PlayerMetricsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlayerMetrics

    player = factory.SubFactory(PlayerProfileFactory)
