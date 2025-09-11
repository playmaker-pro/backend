import factory
from django.conf import settings
from django.db.models import Model
from django.db.utils import ProgrammingError
from faker import Faker
from pydantic import typing

from backend.settings.config import Environment

fake: Faker = Faker()


class CustomObjectFactory(factory.django.DjangoModelFactory):
    """
    Abstract class for our factories where
    we're able to add some factory-based features that fit to our requirements.
    """

    class Meta:
        abstract = True

    @classmethod
    def create(cls, **kwargs) -> Model:
        """Create and save an object to the database."""
        obj = super().create(**kwargs)
        obj.refresh_from_db()
        return obj

    @classmethod
    def random_object(cls, **kwargs) -> Model:
        """get random object from factory's model, unuseable on tests"""
        if settings.CONFIGURATION is not Environment.TEST:
            try:
                return cls._meta.model.objects.filter(**kwargs).order_by("?").first()
            except ProgrammingError:
                pass

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
