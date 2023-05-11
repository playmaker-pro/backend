from unittest import TestCase

from django.test.client import Client
from django.urls import reverse
from rest_framework.response import Response

from . import definitions


class RolesAPITest(TestCase):
    def setUp(self) -> None:
        self.client: Client = Client()
        self.url: str = reverse("api:roles:get_roles")

    def test_method_post_not_allowed(self) -> None:
        """Test if GET method is not allowed"""

        res: Response = self.client.post(self.url)
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

    def test_get_roles_endpoint(self) -> None:
        res: Response = self.client.get(
            self.url,
        )

        assert res.status_code == 200
        expected_roles = {
            role[0]: role[1]
            for role in definitions.ACCOUNT_ROLES
            if role[0] != definitions.PARENT_SHORT
        }
        assert res.data == expected_roles
