from contextlib import contextmanager
from socket import socket
from typing import Optional

from django.conf import settings
from django.db.models import signals
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse
from django.utils import timezone
from factory.django import mute_signals
from rest_framework.response import Response

from clubs.models import Season
from users.models import User
from utils import testutils as utils
from utils.factories.user_factories import UserFactory

utils.silence_explamation_mark()

TEST_EMAIL = "some_email@playmayker.com"


class GetCurrentSeasonTest(TestCase):
    """
    JJ:
    Definicja aktualnego sezonu
    (wyznaczamy go za pomocą:
        jeśli miesiąc daty systemowej jest >= 7
        to pokaż sezon (aktualny rok/ aktualny rok + 1).
        Jeśli < 7 th (aktualny rok - 1 / aktualny rok)
    """

    def setUp(self) -> None:
        settings.SEASON_DEFINITION["middle"] = 7

    def test_season_assign(self):
        tdatas = (
            ((2020, 7, 1), "2020/2021"),
            ((2020, 6, 20), "2019/2020"),
            ((2020, 12, 31), "2020/2021"),
        )
        for date_settings, result in tdatas:
            date = timezone.datetime(*date_settings)
            assert (
                Season.define_current_season(date) == result
            ), f"Input data:{date_settings} date={date}"


@contextmanager
def mute_post_save_signal():
    """Mute post save signal. We don't want to test it in some cases."""
    with mute_signals(signals.post_save):
        yield


class UserManager:
    """
    Utility class for managing user-related operations in tests.
    This class provides convenient methods to create a test user,
    generate an access token for authentication, and retrieve headers with the access
    token for making authenticated requests.
    """

    def __init__(self, client: Optional[Client] = None) -> None:
        self.email = "test_email@test.com"
        self.password = "super secret password"

        if client:
            self.client = client

        self.login_url = reverse("api:users:api-login")

    @mute_post_save_signal()
    def create_superuser(self) -> User:
        """Create a superuser in the test database."""
        user = UserFactory.create(email=self.email, password=self.password)
        user.is_activated = True
        user.save()

        return user

    @property
    def get_access_token(self) -> str:
        """Get the authentication access token for the created superuser."""
        res: Response = self.client.post(
            self.login_url, {"email": self.email, "password": self.password}
        )
        return res.data.get("access")

    def get_headers(self) -> dict:
        """Get the headers containing the authentication token for API requests."""
        headers = {
            "Content-Type": "application/json",
            "content_type": "application/json",
            # "Authorization": "Bearer " + self.get_access_token,
            "HTTP_AUTHORIZATION": f"Bearer {self.get_access_token}",
        }

        return headers

    def login(self, user: User):
        self.client.login(username=user.username, password=user.password)


class MethodsNotAllowedTestsMixin:
    """Test mixin for not allowed methods"""

    NOT_ALLOWED_METHODS = []
    headers = {}

    def test_request_methods_not_allowed(self) -> None:
        """Test request methods not allowed"""

        for element in self.NOT_ALLOWED_METHODS:
            getattr(self, f"{element}_not_allowed")()

    def get_not_allowed(self) -> None:
        """Test if GET method is not allowed"""
        res: Response = self.client.get(self.url, **self.headers)  # noqa
        assert (
            res.status_code == 405
        ), f"Actual response status code is: {res.status_code}, method: GET"

    def post_not_allowed(self) -> None:
        """Test if POST method is not allowed"""

        res: Response = self.client.post(self.url, **self.headers)  # noqa
        assert (
            res.status_code == 405
        ), f"Actual response status code is: {res.status_code}, method: POST"

    def put_not_allowed(self) -> None:
        """Test if PUT method is not allowed"""

        res: Response = self.client.put(self.url, **self.headers)  # noqa
        assert (
            res.status_code == 405
        ), f"Actual response status code is: {res.status_code}, method: PUT"

    def patch_not_allowed(self) -> None:
        """Test if PATCH method is not allowed"""

        res: Response = self.client.patch(self.url, **self.headers)  # noqa
        assert (
            res.status_code == 405
        ), f"Actual response status code is: {res.status_code}, method: PATCH"

    def delete_not_allowed(self) -> None:
        """Test if DELETE method is not allowed"""

        res: Response = self.client.delete(self.url, **self.headers)  # noqa
        assert (
            res.status_code == 405
        ), f"Actual response status code is: {res.status_code}, method: DELETE"


class SocketAccessError(Exception):
    pass


class ExternalCallsGuardMixin:
    @classmethod
    def setUpClass(cls):  # noqa
        cls.socket_original = socket.socket
        socket.socket = cls.guard
        return super().setUpClass()  # noqa

    @classmethod
    def tearDownClass(cls):  # noqa
        socket.socket = cls.socket_original  # noqa
        return super().tearDownClass()  # noqa

    @staticmethod
    def guard(*args, **kwargs):
        raise SocketAccessError("Attempted to access network")


class MockedResponse:
    def __init__(self, json_data, status_code, force_error=False):
        self.force_error = force_error
        self.json_data = json_data
        self.status_code = status_code or 200

    def json(self):
        return self.json_data

    @property
    def ok(self):
        if self.status_code is None:
            return False
        if self.force_error:
            return False
        return self.status_code < 400

    @staticmethod
    def create(**kwargs):
        return MockedResponse(
            status_code=kwargs.get("status_code"), json_data=kwargs.get("json_data")
        )
