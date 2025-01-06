import json as _json

from django.conf import settings as _settings

from payments.models import Transaction as _Transaction
from payments.providers.tpay import schemas as _schemas
from premium.models import Product

_TpayConfig = _settings.ENV_CONFIG.tpay


class TpayTransactionParser:
    def __init__(self, transaction: _Transaction, config: _TpayConfig) -> None:
        self._transaction = transaction
        self._config = config

    @property
    def _payer(self) -> _schemas.TpayPayerData:
        """Get payer data from transaction"""
        return _schemas.TpayPayerData(
            email=self._transaction.user.email,
            name=self._transaction.user.display_full_name,
        )

    @property
    def transaction_body(self) -> _json:
        """Create new transaction body schema to send to tpay"""
        transaction_uuid = str(self._transaction.uuid)
        schema = _schemas.TpayTransactionBody(
            amount=self._transaction.amount,
            description=self._transaction.description,
            hiddenDescription=transaction_uuid,
            payer=self._payer,
            callbacks=self._config.callbacks,
        )
        if self._transaction.product.ref == Product.ProductReference.INQUIRIES:
            schema.callbacks.payerUrls.success += (
                f"&inquiry_count={self._transaction.product.inquiry_plan.limit}"
            )
        schema.callbacks.payerUrls.success += (
            f"&product={self._transaction.product.ref.lower()}"
        )
        print(f"Transaction {transaction_uuid} callback: {schema.callbacks}")
        return schema.json(by_alias=True, exclude_none=True)

    @property
    def auth_body(self) -> _json:
        """Create new auth body schema to send to tpay"""
        return _schemas.TpayAuthBody.from_config(self._config.credentials).json(
            by_alias=True
        )
