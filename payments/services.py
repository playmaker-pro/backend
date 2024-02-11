from uuid import UUID as _UUID

from django.conf import settings as _settings
from django.db.models import QuerySet as _QuerySet

from payments.models import Transaction as _Transaction
from payments.models import TransactionType as _TransactionType


class TransactionService:
    @staticmethod
    def create_new_transaction_object(
        user: _settings.AUTH_USER_MODEL, transaction_type: _TransactionType
    ) -> _Transaction:
        """Create new transaction for given type and user"""
        return _Transaction.objects.create(user=user, transaction_type=transaction_type)

    @staticmethod
    def list_inquiry_transaction_types() -> _QuerySet[_TransactionType]:
        """List transaction types just for inquiries"""
        return _TransactionType.objects.filter(
            ref=_TransactionType.TransactionTypeRef.INQUIRIES, visible=True
        )

    @staticmethod
    def get_transaction_type_by_id(transaction_type_id: int) -> _TransactionType:
        """Get TransactionType by id"""
        return _TransactionType.objects.get(id=transaction_type_id)

    @staticmethod
    def get_transaction_by_uuid(transaction_uuid: _UUID) -> _Transaction:
        """Get Transaction by uuid"""
        return _Transaction.objects.get(uuid=transaction_uuid)
