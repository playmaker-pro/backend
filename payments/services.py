from django.conf import settings as _settings

from payments.models import Transaction as _Transaction
from payments.models import TransactionType as _TransactionType


class TransactionService:
    @staticmethod
    def create_new_transaction_for_inquiry(
        user: _settings.AUTH_USER_MODEL, transaction_type: _TransactionType
    ) -> _Transaction:
        return _Transaction.objects.create(user=user, transaction_type=transaction_type)
