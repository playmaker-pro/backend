from abc import ABCMeta as _ABCMeta
from abc import abstractmethod as _abstractmethod

from app.http.http_service import HttpService as _HttpService
from payments.models import Transaction as _Transaction
from payments.providers.urls import ProviderURLs as _URLs


class BaseTransactionHttpService(_HttpService, metaclass=_ABCMeta):
    def __init__(self, urls: _URLs) -> None:
        super().__init__(urls=urls)
        self._transaction = None

    @_abstractmethod
    def handle(self, transaction: _Transaction):
        self._transaction = transaction
        ...

    @property
    def transaction(self) -> _Transaction:
        self._transaction.refresh_from_db()
        return self._transaction
