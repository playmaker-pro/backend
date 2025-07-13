from urllib.parse import urljoin as _urljoin

from backend.settings import app_config


class TpayURLs:
    _BASE_URL = app_config.tpay.base_url

    TRANSACTION_URL = "/transactions"
    AUTH_URL = "/oauth/auth"

    @property
    def auth_url(self) -> str:
        """URL to authorize tpay client"""
        return _urljoin(self._BASE_URL, self.AUTH_URL)

    @property
    def transaction_url(self) -> str:
        """URL to create tpay transaction"""
        return _urljoin(self._BASE_URL, self.TRANSACTION_URL)
