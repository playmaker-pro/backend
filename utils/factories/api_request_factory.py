import dataclasses
from typing import Type, Any, Union
from rest_framework.response import Response
from rest_framework.test import force_authenticate, APIRequestFactory
from django.http import QueryDict
from urllib.parse import urlencode
from urllib.request import Request
from api.views import EndpointView
from utils import testutils
from typing import Optional
import json
import uuid


@dataclasses.dataclass
class MethodsSet:
    """Set of viewset methods, add methods if needed"""

    GET: Optional[str] = ""
    POST: Optional[str] = ""
    PATCH: Optional[str] = ""

    def __getattribute__(self, name) -> dict:
        """Overwrite attributes to create .as_view() friendly input"""
        return {name.lower(): super().__getattribute__(name)}


class UUIDEncoder(json.JSONEncoder):
    """
    A JSONEncoder subclass that knows how to serialize uuid.UUID objects.

    This is useful when code works with JSON and UUIDs, since the default
    JSONEncoder doesn't know how to serialize UUIDs. Instead of returning the
    UUID object, we return its string representation.
    """

    def default(self, obj: Any) -> Union[str, Any]:
        """
        Overwrite the default method from JSONEncoder.

        If the obj is an instance of uuid.UUID, we return its string representation.
        Otherwise, we call the parent method.
        """
        if isinstance(obj, uuid.UUID):
            # if the obj is uuid, we simply return the value of uuid
            return str(obj)
        return json.JSONEncoder.default(self, obj)


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
        content_type="application/json",
        *args,
        **kwargs,
    ) -> Response:
        """Make post request, return response"""
        request: Request = super().post(
            path, UUIDEncoder().encode(body), content_type=content_type
        )

        return self.response(
            self.methods.POST, request, force_authentication, *args, **kwargs
        )

    def patch(
        self,
        path: str,
        body: dict = None,
        force_authentication: bool = True,
        content_type="application/json",
        *args,
        **kwargs,
    ) -> Response:
        """Make patch request, return response"""
        request: Request = super().patch(
            path, UUIDEncoder().encode(body), content_type=content_type
        )

        return self.response(
            self.methods.PATCH, request, force_authentication, *args, **kwargs
        )
