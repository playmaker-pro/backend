from abc import ABCMeta as _ABCMeta

from app.http.urls import URLs as _URLs


class ProviderURLs(_URLs, metaclass=_ABCMeta):
    ...

    @property
    def auth_url(self) -> str:
        raise NotImplemented

    @property
    def transaction_url(self) -> str:
        raise NotImplemented
