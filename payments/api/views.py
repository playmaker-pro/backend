from rest_framework.permissions import AllowAny
from rest_framework.request import Request as _Request
from rest_framework.response import Response as _Response

from api.views import EndpointView as _EndpointView
from payments.api.serializers import (
    CreateTransactionSerializer as _CreateTransactionSerializer,
)
from payments.services import TransactionService as _TransactionService


class TransactionAPI(_EndpointView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def create_transaction(self, request: _Request) -> _Response:
        """Create transaction"""
        input_serializer = _CreateTransactionSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        transaction = _TransactionService.create_new_transaction_for_inquiry(
            user=request.user, transaction_type=input_serializer.transaction_type
        )
        output_serializer = _CreateTransactionSerializer(transaction)
        #TODO: ...
        return _Response()

    def resolve_transaction(self, request: _Request) -> _Response:
        """Make transaction failed"""
        print(request.data)
        return _Response("TRUE")
