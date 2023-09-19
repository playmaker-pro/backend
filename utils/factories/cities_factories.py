import factory
from cities_light.models import City, Country, Region
from faker import Faker

from app.utils.cities import VOIVODESHIP_MAPPING

from . import utils

fake = Faker()


class CountryFactory(factory.django.DjangoModelFactory):
    name = factory.LazyAttribute(lambda _: fake.name())

    class Meta:
        model = Country


class RegionFactory(factory.django.DjangoModelFactory):
    name = factory.Iterator(list(VOIVODESHIP_MAPPING.keys()))
    country = factory.SubFactory(CountryFactory)

    class Meta:
        model = Region


class CityFactory(factory.django.DjangoModelFactory):
    name = factory.LazyAttribute(lambda _: fake.name())
    country = factory.SubFactory(CountryFactory)
    population = factory.LazyAttribute(lambda _: utils.get_random_int(100, 10000))
    region = factory.SubFactory(RegionFactory)

    class Meta:
        model = City

    @classmethod
    def create_with_coordinates(cls, coordinates: tuple, **kwargs) -> City:
        """Create City with given coordinates"""
        return cls.create(latitude=coordinates[0], longitude=coordinates[1], **kwargs)
