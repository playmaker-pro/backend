from unittest import TestCase
import pytest
from django.test.client import Client
from django.urls import reverse
from rest_framework.response import Response

from . import definitions
from utils.test.test_utils import UserManager


@pytest.mark.django_db
class RolesAPITest(TestCase):
    def setUp(self) -> None:

        self.client: Client = Client()
        self.user = UserManager(self.client)
        self.user_obj = self.user.create_superuser()
        self.headers = self.user.get_headers()
        self.url: str = reverse("api:roles:get-roles")

    def test_method_post_not_allowed(self) -> None:
        """Test if GET method is not allowed"""
        res: Response = self.client.post(self.url, **self.headers)
        assert res.status_code == 405

    def test_method_put_not_allowed(self) -> None:
        """Test if PUT method is not allowed"""

        res: Response = self.client.put(self.url, **self.headers)
        assert res.status_code == 405

    def test_method_patch_not_allowed(self) -> None:
        """Test if PATCH method is not allowed"""

        res: Response = self.client.patch(self.url, **self.headers)
        assert res.status_code == 405

    def test_method_delete_not_allowed(self) -> None:
        """Test if DELETE method is not allowed"""

        res: Response = self.client.delete(self.url, **self.headers)
        assert res.status_code == 405

    def test_get_roles_endpoint(self) -> None:
        """Test get-roles endpoint"""
        res: Response = self.client.get(
            self.url, **self.headers
        )

        assert res.status_code == 200
        expected_roles = {
            role[0]: role[1]
            for role in definitions.ACCOUNT_ROLES
            if role[0] != definitions.PARENT_SHORT
        }
        assert res.data == expected_roles
