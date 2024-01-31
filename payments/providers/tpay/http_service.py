import logging as _logging
import traceback as _traceback

import requests as _requests
from django.conf import settings as _settings

from payments.models import Transaction as _Transaction
from payments.providers import errors as _errors
from payments.providers.base import BaseTransactionHttpService as _HttpService
from payments.providers.tpay import schemas as _schemas
from payments.providers.tpay.parsers import TpayTransactionParser as _Parser
from payments.providers.tpay.urls import TpayURLs as _URLs

_logger = _logging.getLogger("payments")
_config = _settings.ENV_CONFIG


class TpayHttpService(_HttpService):
    _auth: _schemas.TpayAuthResponse = None

    def __init__(self) -> None:
        super().__init__(urls=_URLs)
        self._credentials = _config.tpay.credentials
        self._parser = None

    def handle(self, transaction: _Transaction) -> "TpayHttpService":
        """Handle transaction, ensure an authorization and return service object"""
        self._transaction = transaction
        self._parser = _Parser(transaction, _config.tpay)

        if not self._is_authorized:
            self._authorize()
        return self

    @property
    def _is_authorized(self) -> bool:
        """Check if session is authorized"""
        return self._auth and self._auth.is_valid

    @property
    def _headers(self) -> dict:
        """Get auth headers for session"""
        if not self._is_authorized:
            raise _errors.NotAuthorizedError
        return self._auth.headers

    def _authorize(self) -> None:
        """
        Send authorization request to tpay
        then update session with auth headers.
        """
        try:
            response = self.session.post(
                self.urls.auth_url,
                data=self._parser.auth_body,
            )
            response.raise_for_status()
        except (_requests.HTTPError, _requests.RequestException) as e:
            _logger.error(f"-- AUTH -- {e} -- {_traceback.format_exc()}")
            raise _errors.TransactionError from e

        self._auth = _schemas.TpayAuthResponse.parse_obj(response.json())
        self._update_session_auth_headers()

    def _update_session_auth_headers(self) -> None:
        """Update session headers with auth"""
        self.session.headers.update(self._headers)

    def create_transaction(self) -> _schemas.TpayTransactionResponse:
        """Send create transaction request to tpay and return response"""
        try:
            response = self.session.post(self.urls.transaction_url, data=self._parser.transaction_body)  # type: ignore
            response.raise_for_status()
        except (_requests.HTTPError, _requests.RequestException) as e:
            _logger.error(
                f"-- TRANSACTION -- {e} -- {_traceback.format_exc()}",
            )
            raise _errors.TransactionError from e

        tpay_transaction = _schemas.TpayTransactionResponse.parse_obj(response.json())

        return tpay_transaction
