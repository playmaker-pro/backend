import factory
from django.contrib.auth import get_user_model
from django.db.models import signals

from profiles.models import PlayerMetrics, PlayerProfile
from utils.factories.mapper_factories import MapperFactory

user = get_user_model()
_USER_EMAIL = "unittest@playmaker.pro"


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = user
        django_get_or_create = ("email",)

    email = _USER_EMAIL

    @classmethod
    @factory.django.mute_signals(signals.post_save)
    def create(cls, *args, **kwargs) -> user:
        """Override create() method to hash user password"""
        instance: user = super().create(*args, **kwargs)
        instance.set_password("test")
        instance.save()
        return instance


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
