from typing import Dict, Set
from unittest import TestCase

from django.urls import reverse
import pytest
from rest_framework.response import Response
from rest_framework.test import APITestCase
from rest_framework.test import APIClient
from users.models import User
from utils.test.test_utils import mute_post_save_signal

from api.schemas import RegisterSchema


@pytest.mark.django_db
class TestAuth(APITestCase):
    """Test login, refresh and logout endpoints. Basically JWT token endpoints"""

    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.login_url: str = reverse("api:users:api-login")
        self.refresh_token_url: str = reverse("api:users:api-token-refresh")
        self.logout_url: str = reverse("api:users:api-logout")
        self.user_data: Dict[str, str] = {
            "password": "super secret password",
            "first_name": "first_name",
            "last_name": "last_name",
            "email": "test_email@test.com",
        }
        self.user = self.create_user()

    def login(self) -> Response:
        """Login user and return response"""
        return self.client.post(
            self.login_url,
            data={
                "email": self.user_data["email"],
                "password": self.user_data["password"],
            },
        )

    @mute_post_save_signal()
    def create_user(self) -> User:
        """Create user instance in DB"""
        user: User = User(**self.user_data)
        user.set_password(self.user_data["password"])
        user.save()
        return user

    def test_login_endpoint(self) -> None:
        """Test if login endpoint returns access and refresh tokens"""
        res: Response = self.login()
        assert res.status_code == 200
        assert res.data["refresh"]
        assert res.data["access"]

    def test_not_existing_user_login(self) -> None:
        """Test status code 401 if user does not exist"""
        res: Response = self.client.post(
            self.login_url,
            data={"email": "some@email.com", "password": "some_password"},
        )
        assert res.status_code == 401

    def test_empty_credential_request(self) -> None:
        """Test status code 400 if no credentials in request sent"""
        res: Response = self.client.post(
            self.login_url,
            data={"email": "", "password": ""},
        )
        assert res.status_code == 400

    def test_refresh_token_endpoint(self) -> None:
        """Test if refresh token endpoint returns new access token"""
        res: Response = self.login()
        refresh_token: str = res.data["refresh"]
        refresh_res: Response = self.client.post(
            self.refresh_token_url,
            data={"refresh": refresh_token},
        )
        assert refresh_res.status_code == 200
        assert refresh_res.data["access"]

    def test_if_refresh_tokens_are_different_per_request(self) -> None:
        """Test if tokens are different per request"""
        res: Response = self.login()
        refresh_token: str = res.data["refresh"]
        refresh_res: Response = self.client.post(
            self.refresh_token_url,
            data={"refresh": refresh_token},
        )
        refresh_res2: Response = self.client.post(
            self.refresh_token_url,
            data={"refresh": refresh_token},
        )
        assert refresh_res2.data["access"] != refresh_res.data["access"]

    def test_if_login_tokens_are_different_per_request(self) -> None:
        """Test if tokens are different per request"""
        res: Response = self.login()
        access_token: str = res.data["access"]
        res2: Response = self.login()
        access_token2: str = res2.data["access"]
        assert access_token2 != access_token

    def test_logout_endpoint(self) -> None:
        """Test if logout endpoint returns 200."""
        res: Response = self.login()
        refresh_token: str = res.data["refresh"]
        refresh_res: Response = self.client.post(
            self.logout_url,
            data={"refresh": refresh_token},
        )
        assert refresh_res.status_code == 200


@pytest.mark.django_db
class TestUserCreationEndpoint(TestCase):
    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.url: str = reverse("api:users:api-register")
        self.data: Dict[str, str] = {
            "password": "super secret password",
            "first_name": "first_name",
            "last_name": "last_name",
            "email": "test_email@test.com",
        }

    def test_method_get_not_allowed(self) -> None:
        """Test if GET method is not allowed"""

        res: Response = self.client.get(self.url)
        assert res.status_code == 405

    def test_method_put_not_allowed(self) -> None:
        """Test if PUT method is not allowed"""

        res: Response = self.client.put(self.url)
        assert res.status_code == 405

    def test_method_patch_not_allowed(self) -> None:
        """Test if PATCH method is not allowed"""

        res: Response = self.client.patch(self.url)
        assert res.status_code == 405

    def test_method_delete_not_allowed(self) -> None:
        """Test if DELETE method is not allowed"""

        res: Response = self.client.delete(self.url)
        assert res.status_code == 405

    def test_register_endpoint_response_ok(self) -> None:
        """Test register endpoint. Response OK"""

        res: Response = self.client.post(
            self.url,
            data=self.data,
        )

        assert res.status_code == 200
        assert isinstance(res.data, dict)
        assert res.data["email"] == self.data.get("email")
        assert res.data["id"]
        assert res.data["username"] == self.data.get("email")

    def test_register_endpoint_invalid_mail(self) -> None:
        """Test register endpoint with invalid email field"""

        self.data["email"] = "test_email"
        res: Response = self.client.post(
            self.url,
            data=self.data,
        )

        assert res.status_code == 400
        data: dict = res.json()  # type: ignore

        assert data.get("success") == "False"
        assert data.get("fields") == "email"

    def test_password_not_returned(self) -> None:
        """Test if password field is not returned"""

        res: Response = self.client.post(
            self.url,
            data=self.data,
        )

        assert "password" not in res.data

    def test_doubled_user(self) -> None:
        """Test if user can register account for the second time using the same email"""

        self.client.post(self.url, data=self.data)

        res: Response = self.client.post(
            self.url,
            data=self.data,
        )
        data: dict = res.json()  # type: ignore

        assert res.status_code == 400
        assert data.get("success") == "False"
        assert data.get("fields") == "email"

    def test_response_data(self) -> None:
        """Test if response data contains all required fields from RegisterSchema"""

        user_schema: RegisterSchema = RegisterSchema(**self.data)  # type: ignore
        fields: Set[str] = user_schema.values_fields()
        res: Response = self.client.post(self.url, data=self.data)

        for field in fields:
            assert field in res.data
