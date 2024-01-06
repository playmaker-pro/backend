from abc import ABCMeta as _ABCMeta
from urllib.parse import urljoin as _urljoin

from pydantic import HttpUrl as _HttpUrl


class URLs(metaclass=_ABCMeta):
    _BASE_URL: _HttpUrl

    def _compose_url(self, url: str) -> str:
        """Concat base url with given url (subdir)"""
        return _urljoin(self.base, url)  # type: ignore

    @property
    def base(self) -> _HttpUrl:
        """Get base url"""
        assert self._BASE_URL, "Base url is not set"
        return self._BASE_URL

    @base.setter
    def base(self, url: _HttpUrl) -> None:
        """Set base url"""
        self._BASE_URL = url
