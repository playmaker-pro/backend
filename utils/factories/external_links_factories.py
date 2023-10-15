import factory
from .base import CustomObjectFactory
from external_links.models import LinkSource, ExternalLinks, ExternalLinksEntity


class ExternalLinksFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExternalLinks


class LinkSourceFactory(CustomObjectFactory):
    class Meta:
        model = LinkSource

    name = factory.Sequence(lambda n: f"LinkSource{n}")


class ExternalLinksEntityFactory(factory.django.DjangoModelFactory):
    target = factory.SubFactory(ExternalLinksFactory)
    source = factory.SubFactory(LinkSourceFactory)
    url = "http://example.com"
    related_type = "player"
    creator_type = "user"
    link_type = "statistics"

    class Meta:
        model = ExternalLinksEntity
