from django.conf import settings as _settings

from app.http.urls import URLs as _URLs


class TpayURLs(_URLs):
    _BASE_URL = _settings.ENV_CONFIG.tpay.base_url

    TRANSACTION_URL = "/transactions"
    AUTH_URL = "/oauth/auth"

    @property
    def auth_url(self) -> str:
        """URL to authorize tpay client"""
        return self._compose_url(self.AUTH_URL)

    @property
    def transaction_url(self) -> str:
        """URL to create tpay transaction"""
        return self._compose_url(self.TRANSACTION_URL)
