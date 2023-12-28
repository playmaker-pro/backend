from rest_framework import serializers as _serializers

from payments import models as _models


class NewTransactionSerializer(_serializers.ModelSerializer):
    """Serializer for new transaction"""

    class Meta:
        model = None
        fields = (
            "uuid",
            "transaction_status",
            "transaction_type",
            "payment_method",
            "url",
        )


class CreateTransactionSerializer(_serializers.Serializer):
    """Serializer for create transaction"""

    name = _serializers.CharField(max_length=30)

    def validate_type(self, value: str) -> str:
        """Validate type, check if exist"""
        if value not in _models.TransactionType.objects.all().values_list(
            "name", flat=True
        ):
            raise _serializers.ValidationError("Invalid transaction type name.")
        return value

    @property
    def transaction_type(self) -> _models.TransactionType:
        """Get transaction type"""
        return _models.TransactionType.objects.get(**super().data)
