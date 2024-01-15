from typing import List as _List
from typing import Optional as _Optional

from django.conf import settings as _settings
from pydantic import BaseModel as _BaseModel


class EmailSchema(_BaseModel):
    _sender: str = _settings.DEFAULT_FROM_EMAIL
    type: _Optional[str]

    subject: str
    body: str
    recipients: _List[str]

    @property
    def sender(self) -> str:
        return self._sender

    @sender.setter
    def sender(self, value: str) -> None:
        self._sender = value

    @property
    def log(self) -> str:
        """Return log message. We do not include email body due to user privacy"""
        return (
            f"Title: {self.subject}\nFrom: {self._sender}\n"
            f"Recipients: {self.recipients}\nType: {self.type}"
        )
