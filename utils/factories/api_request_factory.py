import dataclasses
from typing import Type
from rest_framework.response import Response
from rest_framework.test import force_authenticate, APIRequestFactory
from django.http import QueryDict
from urllib.parse import urlencode
from urllib.request import Request
from api.views import EndpointView
from utils import testutils
from typing import Optional


@dataclasses.dataclass
class MethodsSet:
    """Set of viewset methods, add methods if needed"""

    GET: Optional[str] = ""
    POST: Optional[str] = ""
    PATCH: Optional[str] = ""

    def __getattribute__(self, name) -> dict:
        """Overwrite attributes to create .as_view() friendly input"""
        return {name.lower(): super().__getattribute__(name)}


class RequestFactory(APIRequestFactory):
    """
    Requests factory for API testing
    Allows to create HTTP requests for tests use
    Each HTTP method return prepared response
    """

    def __init__(
        self,
        viewset: Type[EndpointView],
        methods: MethodsSet,
        **defaults,
    ):
        self.viewset = viewset
        self.methods = methods
        super().__init__(**defaults)

    @staticmethod
    def parse_payload(payload: dict = None) -> QueryDict:
        """Convert dict to QueryDict to create valid request payload"""
        return QueryDict(urlencode(payload or {}))

    @staticmethod
    def authenticate(request: Request) -> None:
        """Force authenticate request for tests"""
        force_authenticate(request, testutils.get_random_user())

    def response(
        self, method: str, request: Request, authenticate: bool, *args, **kwargs
    ):
        """Generate response out of request"""
        if authenticate:
            self.authenticate(request)
        return self.viewset.as_view(method)(request, *args, **kwargs)

    def get(
        self,
        path: str,
        body: dict = None,
        force_authentication: bool = True,
        *args,
        **kwargs,
    ) -> Response:
        """Make get request, return response"""
        payload: QueryDict = self.parse_payload(body)
        request: Request = super().get(path, payload)
        return self.response(
            self.methods.GET, request, force_authentication, *args, **kwargs
        )

    def post(
        self,
        path: str,
        body: dict = None,
        force_authentication: bool = True,
        *args,
        **kwargs,
    ) -> Response:
        """Make post request, return response"""
        payload: QueryDict = self.parse_payload(body)
        request: Request = super().post(path, payload)
        return self.response(
            self.methods.POST, request, force_authentication, *args, **kwargs
        )

    def patch(
        self,
        path: str,
        body: dict = None,
        force_authentication: bool = True,
        *args,
        **kwargs,
    ) -> Response:
        """Make patch request, return response"""
        payload: QueryDict = self.parse_payload(body)
        request: Request = super().patch(path, payload)
        return self.response(
            self.methods.PATCH, request, force_authentication, *args, **kwargs
        )
