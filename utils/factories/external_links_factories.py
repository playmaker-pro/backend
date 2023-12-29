import factory

from external_links.models import ExternalLinks, ExternalLinksEntity, LinkSource

from .base import CustomObjectFactory


class ExternalLinksFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExternalLinks


class LinkSourceFactory(CustomObjectFactory):
    class Meta:
        model = LinkSource

    name = factory.LazyAttribute(lambda obj: f"LinkSource{LinkSource.objects.count()}")

    @classmethod
    def _create(cls, model_class, *args, **kwargs) -> LinkSource:
        """
        This method is overridden to handle the creation of LinkSource instances. It checks if a 'name'
        argument is provided in kwargs. If so, it attempts to get or create a LinkSource instance with
        the provided name. If no 'name' is provided, it defaults to the standard factory creation process.
        """
        name = kwargs.get("name")
        if name:
            link_source, _ = LinkSource.objects.get_or_create(name=name)
        else:
            link_source = super()._create(model_class, *args, **kwargs)
        return link_source


class ExternalLinksEntityFactory(factory.django.DjangoModelFactory):
    target = factory.SubFactory(ExternalLinksFactory)
    source = factory.SubFactory(LinkSourceFactory)
    url = "http://example.com"
    related_type = "player"
    creator_type = "user"
    link_type = "statistics"

    class Meta:
        model = ExternalLinksEntity
