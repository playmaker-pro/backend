from django.http import HttpResponse as _HttpResponse
from rest_framework import status as _status
from rest_framework.exceptions import PermissionDenied as _PermissionDenied
from rest_framework.permissions import AllowAny as _AllowAny
from rest_framework.request import Request as _Request
from rest_framework.response import Response as _Response

from api.views import EndpointView as _EndpointView
from payments.api import serializers as _serializers
from payments.logging import logger as _logger
from payments.models import TransactionType as _TransactionType
from payments.providers.errors import TransactionError as _TransactionError
from payments.providers.tpay import schemas as _tpay_schemas
from payments.providers.tpay.http_service import TpayHttpService as _TpayHttpService
from payments.providers.tpay.validators import (
    TpayResponseValidator as _TpayResponseValidator,
)
from payments.services import TransactionService as _TransactionService

_TpayProvider = _TpayHttpService()


class TransactionAPI(_EndpointView):
    def create_transaction_for_type(
        self, request: _Request, transaction_type_id: int
    ) -> _Response:
        """Create transaction"""
        try:
            transaction_type = _TransactionService.get_transaction_type_by_id(
                transaction_type_id
            )
        except _TransactionType.DoesNotExist:
            return _Response(
                "Invalid transaction type id.",
                status=_status.HTTP_400_BAD_REQUEST,
            )

        if not transaction_type.visible and not request.user.is_staff:
            raise _PermissionDenied

        transaction = _TransactionService.create_new_transaction_object(
            user=request.user, transaction_type=transaction_type
        )

        try:
            transaction = _TpayProvider.handle(transaction)
        except _TransactionError:
            return _Response(
                "Something went wrong. Try again later.",
                status=_status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        serializer = _serializers.NewTransactionSerializer(transaction)
        return _Response(serializer.data)

    def list_inquiry_transaction_types(self, request: _Request) -> _Response:
        """List transaction types"""
        qs = _TransactionService.list_inquiry_transaction_types()
        serializer = _serializers.TransactionTypeSerializer(qs, many=True)
        return _Response(serializer.data)


class TpayWebhook(_EndpointView):
    permission_classes = [_AllowAny]
    authentication_classes = []

    def resolve_transaction(self, request: _Request) -> _HttpResponse:
        """Resolve notification from tpay"""
        schema = _tpay_schemas.TpayTransactionResult.parse_obj(request.data.dict())
        validator = _TpayResponseValidator.handle(schema)
        if validator.is_valid:
            _logger.info(f"-- RESOLVE ({validator.crc}) -- SUCCESS")
        else:
            _logger.error(f"-- RESOLVE ({validator.crc}) -- ERRORS: {validator.errors}")
        validator.resolve_transaction()
        return _HttpResponse("TRUE")
