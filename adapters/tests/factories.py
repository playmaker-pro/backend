from django.contrib.auth import get_user_model
from profiles.models import PlayerProfile
import factory
from mapper.models import Mapper, MapperEntity, MapperSource

user = get_user_model()

_ID = "111222333"
_USER_EMAIL = "unittest@playmaker.pro"
MAPPER_SOURCE_NAME = "TEST"
MAPPER_DATABASE_SOURCE = "scrapper_mongodb"
MAPPER_PLAYER_TYPE = "player"


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = user
        django_get_or_create = ("email",)

    email = _USER_EMAIL


class MapperFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Mapper


class MapperSourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MapperSource


class MapperEntityFactory(factory.django.DjangoModelFactory):

    mapper_id = _ID
    target = factory.SubFactory(MapperSourceFactory)
    source = factory.SubFactory(MapperSourceFactory)
    related_type = MAPPER_PLAYER_TYPE
    database_source = MAPPER_DATABASE_SOURCE

    def __init__(self, target):
        self.target = target

    class Meta:
        model = MapperEntity
        django_get_or_create = ("mapper_id",)


class PlayerProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlayerProfile
        django_get_or_create = ("user",)

    user = factory.SubFactory(UserFactory)
    mapper = factory.SubFactory(MapperFactory)
