import uuid as _uuid
from decimal import Decimal as _Decimal
from typing import List as _List

from django.conf import settings as _settings
from django.db import models as models
from django_fsm import FSMField as _FSMField
from django_fsm import transition as _transition

from inquiries.models import InquiryPlan
from payments.logging import logger as _logger
from payments.providers.tpay import schemas as _tpay_schemas


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
        self.change_user_plan()
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

    def change_user_plan(self) -> None:
        """Change user plan based on a transaction type"""
        plan = InquiryPlan.objects.get(type_ref=self.product.name)
        self.user.userinquiry.set_new_plan(plan)

    def __str__(self) -> str:
        return (
            f"{self.uuid} -- "
            f"{self.user.display_full_name} -- "
            f"{self.transaction_type_readable_name} -- "
            f"{self.created_at} -- "
            f"{self.transaction_status}"
        )
