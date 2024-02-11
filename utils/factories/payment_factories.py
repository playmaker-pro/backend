import factory

from payments.models import Transaction, TransactionType
from utils.factories import UserFactory


class TransactionTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TransactionType
        django_get_or_create = ("name",)

    name = "Test Type"
    name_readable = "Test Type Readable"
    price = 10.00
    ref = TransactionType.TransactionTypeRef.INQUIRIES


class TransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Transaction
        django_get_or_create = (
            "uuid",
            "user",
        )

    user = factory.SubFactory(UserFactory)
    transaction_type = factory.SubFactory(TransactionTypeFactory)
