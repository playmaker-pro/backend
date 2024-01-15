from abc import ABCMeta as _ABCMeta
from typing import Type as _Type

import requests as _requests

from app.http.urls import URLs as _URLs


class HttpService(metaclass=_ABCMeta):
    _urls: _URLs
    # TODO: THIS SHOULD USE HTTP SERIVCE FROM PM-CORE BUT WE DONT HAVE VERSIONING YET

    def __init__(
        self, session: _requests.Session = None, urls: _Type[_URLs] = None
    ) -> None:
        """
        Initialize the HttpService with a requests.Session object.

        :param session: A requests.Session object for making HTTP requests.
        """
        self.session: _requests.Session = session or self._set_session()
        if urls:
            self.urls = urls()

    @property
    def urls(self) -> _URLs:
        """Get urls"""
        assert self._urls, "Urls are not set"
        return self._urls

    @urls.setter
    def urls(self, urls: _URLs) -> None:
        """Set urls"""
        self._urls = urls

    def _set_session(self) -> _requests.Session:
        """
        Create and return a new requests.Session object.
        Set authentication headers.

        :return: A new requests.Session object.
        """
        return _requests.Session()

    def _get(self, url: str, **params) -> _requests.Response:
        """
        Make a GET request to the specified URL and return json response.

        :param url: The URL to make the GET request to.
        :param params: The parameters to pass to the GET request.
        :return: The response from the GET request.
        """
        # TODO: As said above, this should use HTTP service from pm-core
        response = self.session.get(url=url, params=params)
        response.raise_for_status()
        return response
