import uuid as _uuid
from decimal import Decimal as _Decimal
from typing import List as _List

from django.conf import settings as _settings
from django.db import models as models
from django_fsm import FSMField as _FSMField
from django_fsm import transition as _transition

from roles.definitions import PROFILE_TYPE_FULL_MAP, PROFILE_TYPE_OTHER
from payments.logging import logger as _logger
from payments.providers.tpay import schemas as _tpay_schemas
from django.utils.translation import gettext as _


class Transaction(models.Model):
    class TransactionStatus(models.TextChoices):
        PENDING = "PENDING", "PENDING"
        SUCCESS = "SUCCESS", "SUCCESS"
        FAILED = "FAILED", "FAILED"
        OUTDATED = "OUTDATED", "OUTDATED"

    class TransactionError(models.TextChoices):
        OVERPAID = "overpay", "OVERPAID"
        UNDERPAID = "surcharge", "UNDERPAID"
        NONE = "none", "NONE"

    uuid = models.UUIDField(default=_uuid.uuid4, editable=False, primary_key=True)

    user = models.ForeignKey(_settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    transaction_status = _FSMField(
        choices=TransactionStatus.choices, default=TransactionStatus.PENDING
    )
    product = models.ForeignKey("premium.Product", on_delete=models.PROTECT)
    error = models.CharField(
        choices=TransactionError.choices, max_length=30, null=True, blank=True
    )
    validation_errors = models.TextField(null=True, blank=True)

    raw_create_response = models.JSONField(null=True, blank=True)
    raw_resolve_response = models.JSONField(null=True, blank=True)
    url = models.URLField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @_transition(
        transaction_status,
        source=TransactionStatus.PENDING,
        target=TransactionStatus.SUCCESS,
    )
    def success(self) -> None:
        """Set transaction status as SUCCESS"""
        self.product.apply_product_for_transaction(self)
        _logger.info(
            f"Transaction {self.uuid} for user ID={self.user.pk} has been approved."
        )

    @_transition(
        transaction_status,
        source=TransactionStatus.PENDING,
        target=TransactionStatus.FAILED,
    )
    def failed(self) -> None:
        """Set transaction status as FAILED"""

    @_transition(
        transaction_status,
        source=TransactionStatus.PENDING,
        target=TransactionStatus.OUTDATED,
    )
    def outdated(self) -> None:
        """Set transaction status as OUTDATED"""
        # TODO: may be implemented with celery to mark transaction as outdated after some time
        raise NotImplementedError

    @property
    def amount(self) -> _Decimal:
        """Get transaction amount from a transaction type"""
        return self.product.price

    @property
    def transaction_type_readable_name(self) -> str:
        """Get transaction type readable name"""
        return self.product.name_readable

    @property
    def description(self) -> str:
        """Prepare description based on a transaction type"""
        return f"PLAYMAKER.PRO | {self.transaction_type_readable_name}"

    def update_from_dict(self, data: dict) -> None:
        """Update a transaction object from dictionary"""
        self.__dict__.update(**data)
        self.save()

    def get_localized_description(self) -> str:
        """Prepare localized description using the currently activated language"""
        # Get profile type from user
        user_profile = getattr(self.user, "profile", None)

        # map profile types to their translatable display names from definitions
        if user_profile:
            profile_type_key = user_profile.PROFILE_TYPE
            profile_display_name = PROFILE_TYPE_FULL_MAP.get(
                profile_type_key, PROFILE_TYPE_FULL_MAP[PROFILE_TYPE_OTHER]
            )
        else:
            profile_display_name = PROFILE_TYPE_FULL_MAP[PROFILE_TYPE_OTHER]

        # Get the base name and append the profile type
        base_description = _(self.product.name_readable)
        profile_type_translated = _(profile_display_name)
        full_description = f"{base_description} {profile_type_translated}"

        return f"PLAYMAKER.PRO | {full_description}"

    def resolve_from_tpay_schema(
        self, schema: _tpay_schemas.TpayTransactionResult, errors: _List[str]
    ) -> None:
        """Resolve transaction based on validated tpay response schema"""
        self.raw_resolve_response = schema.json(by_alias=True)
        self.error = self.TransactionError(schema.tr_error)

        if errors:
            self.validation_errors = ". ".join(errors)
            self.failed()
        else:
            self.success()
        self.save()

    def __str__(self) -> str:
        return (
            f"{self.uuid} -- "
            f"{self.user.display_full_name} -- "
            f"{self.transaction_type_readable_name} -- "
            f"{self.created_at} -- "
            f"{self.transaction_status}"
        )
