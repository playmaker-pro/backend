import logging as _logging
import uuid as _uuid
from decimal import Decimal as _Decimal

from django.conf import settings as _settings
from django.db import models as _models
from django_fsm import FSMField as _FSMField
from django_fsm import transition as _transition

from inquiries.models import InquiryPlan as _InquiryPlan
from payments.providers.tpay import schemas as _tpay_schemas

_logger = _logging.getLogger("payments")


class Transaction(_models.Model):
    class TransactionStatus(_models.TextChoices):
        PENDING = "PENDING", "PENDING"
        SUCCESS = "SUCCESS", "SUCCESS"
        FAILED = "FAILED", "FAILED"
        OUTDATED = "OUTDATED", "OUTDATED"

    class TransactionError(_models.TextChoices):
        OVERPAID = "overpay", "OVERPAID"
        UNDERPAID = "surcharge", "UNDERPAID"
        NONE = "none", "NONE"

    uuid = _models.UUIDField(default=_uuid.uuid4, editable=False, primary_key=True)

    user = _models.ForeignKey(_settings.AUTH_USER_MODEL, on_delete=_models.CASCADE)
    transaction_status = _FSMField(
        choices=TransactionStatus.choices, default=TransactionStatus.PENDING
    )
    transaction_type = _models.ForeignKey("TransactionType", on_delete=_models.PROTECT)
    error = _models.CharField(
        choices=TransactionError.choices, max_length=30, null=True, blank=True
    )

    raw_create_response = _models.JSONField(null=True, blank=True)
    raw_resolve_response = _models.JSONField(null=True, blank=True)
    url = _models.URLField(null=True, blank=True)

    created_at = _models.DateTimeField(auto_now_add=True)
    updated_at = _models.DateTimeField(auto_now=True)

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
    def failed(self, error: str) -> None:
        """Set transaction status as FAILED"""
        _logger.info(f"Transaction {self.uuid} failed, error: {error}")

    @_transition(
        transaction_status,
        source=TransactionStatus.PENDING,
        target=TransactionStatus.OUTDATED,
    )
    def outdated(self) -> None:
        """Set transaction status as OUTDATED"""
        # TODO: may be implemented with celery to mark transaction as outdated after some time

    @property
    def amount(self) -> _Decimal:
        """Get transaction amount from a transaction type"""
        return self.transaction_type.price

    @property
    def transaction_type_readable_name(self) -> str:
        """Get transaction type readable name"""
        return self.transaction_type.name_readable

    @property
    def description(self) -> str:
        """Prepare description based on a transaction type"""
        return f"PLAYMAKER.PRO | {self.transaction_type_readable_name}"

    def update_from_dict(self, data: dict) -> None:
        """Update a transaction object from dictionary"""
        self.__dict__.update(**data)
        self.save()

    def resolve_from_tpay_schema(
        self, schema: _tpay_schemas.TpayTransactionResult
    ) -> None:
        """Resolve transaction based on validated tpay response schema"""
        self.raw_resolve_response = schema.json(by_alias=True)
        self.error = self.TransactionError(schema.tr_error)

        try:
            schema.post_validate()
        except AttributeError as e:
            self.failed(str(e))
        else:
            self.success()
        finally:
            self.save()

    def change_user_plan(self) -> None:
        """Change user plan based on a transaction type"""
        plan = self.transaction_type.inquiry_plan
        self.user.userinquiry.set_new_plan(plan)

    def __str__(self) -> str:
        return (
            f"{self.uuid} -- "
            f"{self.user.display_full_name} -- "
            f"{self.transaction_type_readable_name} -- "
            f"{self.created_at} -- "
            f"{self.transaction_status}"
        )


class TransactionType(_models.Model):
    class TransactionTypeRef(_models.TextChoices):
        INQUIRIES = "INQUIRIES", "INQUIRIES"
        ...

    name = _models.CharField(max_length=30, unique=True)
    name_readable = _models.CharField(max_length=50)
    price = _models.DecimalField(decimal_places=2, max_digits=5)
    ref = _models.CharField(max_length=30, choices=TransactionTypeRef.choices)
    visible = _models.BooleanField(default=True)

    @property
    def inquiry_plan(self) -> _InquiryPlan:
        """Get inquiry plan related to the transaction type"""
        return _InquiryPlan.objects.get(type_ref=self.name)

    def __str__(self) -> str:
        return f"{self.ref} -- {self.name} -- {self.name_readable} -- {self.price}"
