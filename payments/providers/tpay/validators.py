import hashlib as _hashlib
import typing as _typing
from uuid import UUID as _UUID

from backend.settings import cfg
from payments.models import Transaction as _Transaction
from payments.providers.tpay import schemas as _schemas
from payments.services import TransactionService as _TransactionService


class TpayResponseValidator:
    """Validator for tpay transaction response"""

    def __init__(self, schema: _schemas.TpayTransactionResult) -> None:
        self._schema = schema
        self._initialized = False
        self._errors: _typing.List[str] = []

    @property
    def crc(self) -> _UUID:
        """Get crc from response (our object uuid)"""
        return self._schema.tr_crc

    @property
    def transaction(self) -> _typing.Optional[_Transaction]:
        """Get transaction object from database, return None if it does not exist"""
        try:
            return _TransactionService.get_transaction_by_uuid(self.crc)
        except _Transaction.DoesNotExist:
            return

    def _validate_md5_checksum(self) -> None:
        """Validate md5 checksum of tpay response"""
        to_hash = self._schema.prepare_to_hash(secret=cfg.tpay.security_code).encode(
            "utf-8"
        )

        md5_hash = _hashlib.md5()
        md5_hash.update(to_hash)

        if md5_hash.hexdigest() != self._schema.md5sum:
            self._errors.append(_schemas.TpayValidationErrors.INVALID_MD5.value)

    def _compare_with_object(self) -> None:
        """Compare transaction that came from tpay with object in database"""
        transaction = self.transaction

        if transaction is None:
            self._errors.append(
                _schemas.TpayValidationErrors.TRANSACTION_NOT_FOUND.value
            )
            return

        if transaction.amount != self._schema.tr_amount:
            self._errors.append(_schemas.DataAssertingErrors.AMOUNT.parse_full)
        if transaction.uuid != self._schema.tr_crc:
            self._errors.append(_schemas.DataAssertingErrors.UUID.parse_full)
        if transaction.description != self._schema.tr_desc:
            self._errors.append(_schemas.DataAssertingErrors.DESCRIPTION.parse_full)

    def _check_test_mode(self):
        if self._schema.test_mode.is_test and not cfg.tpay.test_mode:
            self._errors.append(
                _schemas.TpayValidationErrors.TEST_MODE_NOT_ALLOWED.value
            )

    def validate(self) -> None:
        """Perform validation for transaction response"""
        self._check_test_mode()
        self._validate_md5_checksum()
        self._compare_with_object()

        self._initialized = True

    @classmethod
    def handle(cls, schema: _schemas.TpayTransactionResult) -> "TpayResponseValidator":
        """
        Handle transaction response validation,
        return validator object itself after validation
        """
        validator = cls(schema)
        validator.validate()
        return validator

    @property
    def is_valid(self) -> bool:
        """Check if transaction is valid"""
        return self._initialized and not self._errors

    @property
    def errors(self) -> _typing.List[str]:
        """Get all occurred errors"""
        return self._errors

    def resolve_transaction(self) -> None:
        """Assert that transaction response is valid, then perform transaction object resolve"""
        self.transaction.resolve_from_tpay_schema(self._schema, self.errors)
