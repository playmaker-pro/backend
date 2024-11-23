from uuid import UUID as _UUID

from django.conf import settings

from payments.models import Transaction
from payments.providers.tpay.http_service import TpayHttpService
from premium.models import Product


class TransactionService:
    def __init__(self, transaction: Transaction) -> None:
        self.transaction = transaction
        self.provider = TpayHttpService()

    @classmethod
    def create_new_transaction_object(
        cls, user: settings.AUTH_USER_MODEL, product: Product
    ) -> Transaction:
        """Create new transaction for given type and user"""
        transaction = Transaction.objects.create(user=user, product=product)
        return cls(transaction)

    @staticmethod
    def get_transaction_by_uuid(transaction_uuid: _UUID) -> Transaction:
        """Get Transaction by uuid"""
        return Transaction.objects.get(uuid=transaction_uuid)

    def handle(self) -> Transaction:
        """Handle transaction"""
        return self.provider.handle(self.transaction)
