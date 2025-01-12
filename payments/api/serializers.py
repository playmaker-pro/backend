from rest_framework import serializers as _serializers

from payments import models as _models


class NewTransactionSerializer(_serializers.ModelSerializer):
    """Serializer for new transaction"""

    class Meta:
        model = _models.Transaction
        fields = (
            "uuid",
            "url",
        )
