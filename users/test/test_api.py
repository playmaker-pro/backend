from typing import Dict, Set
from unittest import TestCase

from django.test.client import Client
from django.urls import reverse
import pytest
from rest_framework.response import Response

from api.schemas import RegisterSchema


@pytest.mark.django_db
class TestUserCreationEndpoint(TestCase):
    def setUp(self) -> None:
        self.client: Client = Client()
        self.url: str = reverse("users:api-register")
        self.data: Dict[str, str] = {
            "password": "super secret password",
            "first_name": "first_name",
            "last_name": "last_name",
            "email": "test_email@test.com",
        }

    def invalid_email(self) -> None:
        self.data["email"] = "test_email"

    def valid_email(self) -> None:
        self.data["email"] = "test_email@test.com"

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

        self.invalid_email()
        res: Response = self.client.post(
            self.url,
            data=self.data,
        )

        assert res.status_code == 400
        assert "email" in res.data

        self.valid_email()

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

        assert res.status_code == 400

    def test_response_data(self) -> None:
        """Test if response data contains all required fields from RegisterSchema"""

        user_schema: RegisterSchema = RegisterSchema(**self.data)
        fields: Set[str] = user_schema.values_fields()
        res: Response = self.client.post(self.url, data=self.data)

        for field in fields:
            assert field in res.data
