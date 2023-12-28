import uuid as _uuid

from django.conf import settings as _settings
from django.db import models as _models
from django_fsm import FSMField as _FSMField
from django_fsm import transition as _transition


class Transaction(_models.Model):
    class TransactionStatus(_models.TextChoices):
        PENDING = "PENDING", "PENDING"
        SUCCESS = "SUCCESS", "SUCCESS"
        FAILED = "FAILED", "FAILED"
        OUTDATED = "OUTDATED", "OUTDATED"

    class Currency(_models.TextChoices):
        PLN = "PLN", "PLN"
        EUR = "EUR", "EUR"
        USD = "USD", "USD"

    class PaymentMethod(_models.TextChoices):
        TRANSFER = "TRANSFER", "TRANSFER"
        BLIK = "BLIK", "BLIK"

    class TransactionError(_models.TextChoices):
        OVERPAID = "OVERPAID", "OVERPAID"
        UNDERPAID = "UNDERPAID", "UNDERPAID"

    uuid = _models.UUIDField(default=_uuid.uuid4, editable=False, primary_key=True)

    user = _models.ForeignKey(_settings.AUTH_USER_MODEL, on_delete=_models.CASCADE)
    transaction_status = _FSMField(
        choices=TransactionStatus.choices, default=TransactionStatus.PENDING
    )
    transaction_type = _models.ForeignKey("TransactionType", on_delete=_models.PROTECT)
    payment_method = _models.CharField(choices=PaymentMethod.choices, max_length=30, null=True, blank=True)
    error = _models.CharField(
        choices=TransactionError.choices, max_length=30, null=True, blank=True
    )

    created_at = _models.DateTimeField(auto_now_add=True)
    updated_at = _models.DateTimeField(auto_now=True)

    @_transition(
        transaction_status,
        source=TransactionStatus.PENDING,
        target=TransactionStatus.SUCCESS,
    )
    def success(self) -> None:
        """Set transaction status as SUCCESS"""

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

    class TransactionManager(_models.Manager):
        def resolve(self):
            ...

    objects = TransactionManager()


class TransactionType(_models.Model):
    class TransactionTypeRef(_models.TextChoices):
        INQUIRIES = "INQUIRIES", "INQUIRIES"

    name = _models.CharField(max_length=30, unique=True)
    name_readable = _models.CharField(max_length=50)
    price = _models.DecimalField(decimal_places=2, max_digits=5)
    ref = _models.CharField(max_length=30, choices=TransactionTypeRef.choices)

    class TransactionTypeManager(_models.Manager):
        @property
        def inquiries5(self) -> "TransactionType":
            return self.get(name="PREMIUM_INQUIRIES_5")

        @property
        def inquiries10(self) -> "TransactionType":
            return self.get(name="PREMIUM_INQUIRIES_10")

        @property
        def inquiries25(self) -> "TransactionType":
            return self.get(name="PREMIUM_INQUIRIES_25")

    objects = TransactionTypeManager()
