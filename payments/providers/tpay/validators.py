import hashlib as _hashlib
import typing as _typing
from uuid import UUID as _UUID

from django.conf import settings as _settings

from payments.models import Transaction as _Transaction
from payments.providers.tpay import schemas as _schemas
from payments.services import TransactionService as _TransactionService

_config = _settings.ENV_CONFIG


class TpayResponseValidator:
    """Validator for tpay transaction response"""

    def __init__(self, schema: _schemas.TpayTransactionResult) -> None:
        self._schema = schema
        self._initialized = False
        self._errors: _typing.List[_schemas.TpayValidationErrors] = []

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

    def validate_md5_checksum(self) -> None:
        """Validate md5 checksum of tpay response"""
        to_hash = self._schema.prepare_to_hash(
            secret=_config.tpay.security_code
        ).encode("utf-8")

        md5_hash = _hashlib.md5()
        md5_hash.update(to_hash)

        if md5_hash.hexdigest() != self._schema.md5sum:
            self._errors.append(_schemas.TpayValidationErrors.INVALID_MD5)

    def compare_with_object(self) -> None:
        """Compare transaction that came from tpay with object in database"""
        transaction = self.transaction

        if transaction is None:
            self._errors.append(_schemas.TpayValidationErrors.TRANSACTION_NOT_FOUND)
            return

        try:
            assert (
                transaction.amount == self._schema.tr_amount
            ), _schemas.DataAssertingErrors.AMOUNT
            assert (
                transaction.uuid == self._schema.tr_crc
            ), _schemas.DataAssertingErrors.UUID
            assert (
                transaction.description == self._schema.tr_desc
            ), _schemas.DataAssertingErrors.DESCRIPTION
        except AssertionError as e:
            self._errors.append(e.args[0].parse_full)  # type: ignore

    def validate(self) -> None:
        """Perform validation for transaction response"""
        self.validate_md5_checksum()
        self.compare_with_object()
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
        assert self.is_valid, "Unable to resolve invalid transaction."
        self.transaction.resolve_from_tpay_schema(self._schema)
