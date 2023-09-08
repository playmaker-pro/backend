from cities_light.models import City, Country, Region
import factory
from app.utils.cities import VOIVODESHIP_MAPPING
from . import utils
from faker import Faker

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
