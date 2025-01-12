from django.http import HttpResponse as _HttpResponse
from rest_framework.permissions import AllowAny as _AllowAny
from rest_framework.request import Request as _Request

from api.views import EndpointView as _EndpointView
from payments.logging import logger as _logger
from payments.providers.tpay import schemas as _tpay_schemas
from payments.providers.tpay.validators import (
    TpayResponseValidator as _TpayResponseValidator,
)


class TpayWebhook(_EndpointView):
    permission_classes = [_AllowAny]
    authentication_classes = []

    def resolve_transaction(self, request: _Request) -> _HttpResponse:
        """Resolve notification from tpay"""
        schema = _tpay_schemas.TpayTransactionResult.parse_obj(request.data.dict())
        validator = _TpayResponseValidator.handle(schema)
        if validator.is_valid:
            _logger.info(f"-- RESOLVE ({validator.crc}) -- SUCCESS")
            response = _HttpResponse("TRUE")
        else:
            _logger.error(f"-- RESOLVE ({validator.crc}) -- ERRORS: {validator.errors}")
            response = _HttpResponse("FALSE")
        validator.resolve_transaction()
        return response
