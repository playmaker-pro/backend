import uuid
import factory

from payments.models import Transaction
from utils.factories import UserFactory
from utils.factories.premium_factories import ProductFactory


class TransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Transaction
        django_get_or_create = (
            "uuid",
            "user",
        )

    user = factory.SubFactory(UserFactory)
    uuid = factory.LazyFunction(uuid.uuid4)
