import factory
from mapper.models import Mapper, MapperSource, MapperEntity

ID = "111222333"
MAPPER_DATABASE_SOURCE = "scrapper_mongodb"
MAPPER_PLAYER_TYPE = "player"


class MapperFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Mapper


class MapperSourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MapperSource


class MapperEntityFactory(factory.django.DjangoModelFactory):

    mapper_id = ID
    target = factory.SubFactory(MapperSourceFactory)
    source = factory.SubFactory(MapperSourceFactory)
    related_type = MAPPER_PLAYER_TYPE
    database_source = MAPPER_DATABASE_SOURCE

    def __init__(self, target):
        self.target = target

    class Meta:
        model = MapperEntity
        django_get_or_create = ("mapper_id",)
