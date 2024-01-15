import logging

import factory
from django.conf import settings
from django.db.models import Model
from django.db.utils import ProgrammingError
from faker import Faker
from pydantic import typing

from backend.settings.environment import Environment

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
        if env() is not Environment.TEST:
            logger.info(
                f"[Factory: {cls.__name__}, model: "
                f"{type(obj)}] Object: ID={obj.pk} | {obj}",
            )
        return obj

    @classmethod
    def create(cls, **kwargs) -> Model:
        """
        Overwrite crate() method to log if something went wrong with saving new objects
        """
        try:
            return super().create(**kwargs)
        except Exception as e:
            logger.error(e)
            raise e

    @classmethod
    def random_object(cls, **kwargs) -> Model:
        """get random object from factory's model, unuseable on tests"""
        if env() is not Environment.TEST:
            try:
                return cls._meta.model.objects.filter(**kwargs).order_by("?").first()
            except ProgrammingError:
                pass

    @classmethod
    def get_random_or_create_subfactory(
        cls, **kwargs
    ) -> typing.Union[Model, factory.SubFactory]:
        """Get random object or create subfactory of class"""
        random_object: Model = cls.random_object(**kwargs)
        return (
            random_object or factory.SubFactory(cls, **kwargs)
            if env() is not Environment.TEST
            else None
        )

    @classmethod
    def transform_dict(cls, json_data: dict) -> dict:
        """
        Parse dictionary to define nested fields among sub-factories
        {team: {club: {name: ...}}} -> team__club__name
        """
        transformed_data = {}

        def transform_keys(data: typing.Union[str, list, dict], prefix=""):
            if isinstance(data, dict):
                for key, value in data.items():
                    new_key = f"{prefix}__{key}" if prefix else key
                    transform_keys(value, prefix=new_key)
            elif isinstance(data, list):
                for item in data:
                    transform_keys(item, prefix=prefix)
            else:
                transformed_data[prefix] = data

        transform_keys(json_data)
        return transformed_data

    @classmethod
    def create_from_dict(cls, data: dict) -> Model:
        """Mock objects supplied by dictionary"""
        kwargs = cls.transform_dict(data)
        cls.set_subfactories()
        return cls.create(**kwargs)

    @classmethod
    def set_subfactories(cls) -> None:
        """
        Abstract method that should be overwritten when factory needs
        to add sub factories
        """
