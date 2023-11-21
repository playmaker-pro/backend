from typing import List as _List

from django.conf import settings as _settings
from pydantic import BaseModel as _BaseModel


class EmailSchema(_BaseModel):
    _sender: str = _settings.DEFAULT_FROM_EMAIL

    subject: str
    body: str
    recipients: _List[str]

    @property
    def sender(self) -> str:
        return self._sender

    @sender.setter
    def sender(self, value: str) -> None:
        self._sender = value
