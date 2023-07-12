import factory
import logging
from faker import Faker
from django.db.models import Model
from django.conf import settings
from pydantic import typing

logger: logging.Logger = logging.getLogger("mocker")
fake: Faker = Faker()


def env() -> str:
    """get environment from settings"""
    return settings.CONFIGURATION


class CustomObjectFactory(factory.django.DjangoModelFactory):
    """
    Abstract class for our factories where
    we're able to add some factory-based features that fit to our requirements.
    """

    class Meta:
        abstract = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs) -> Model:
        """Overwrite _create() method to log results"""
        obj: Model = super()._create(model_class, *args, **kwargs)
        if env() != "test":
            logger.info(
                f"[Factory: {cls.__name__}, model: {type(obj)}] Object: ID={obj.pk} | {obj}",
            )
        return obj

    @classmethod
    def random_object(cls, **kwargs) -> Model:
        """get random object from factory's model, unuseable on tests"""
        if env() != "test":
            return cls._meta.model.objects.filter(**kwargs).order_by("?").first()

    @classmethod
    def get_random_or_create_subfactory(
        cls, **kwargs
    ) -> typing.Union[Model, factory.SubFactory]:
        """Get random object or create subfactory of class"""
        random_object: Model = cls.random_object(**kwargs)
        return (
            random_object or factory.SubFactory(cls, **kwargs)
            if env() == "test"
            else None
        )
