import base64
from typing import Dict
from unittest import TestCase

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from drf_yasg.openapi import Swagger
from rest_framework.exceptions import ErrorDetail
from rest_framework.response import Response
from rest_framework.test import APIClient

from utils.factories.user_factories import UserFactory
from utils.test.test_utils import mute_post_save_signal

user = get_user_model()


@pytest.mark.django_db
class UserSwaggerTestCase(TestCase):
    """Test case for swagger endpoint"""

    def setUp(self):
        """Set up test case."""
        self.url: str = reverse("schema-swagger-ui")
        self.user: user = UserFactory.create(is_staff=False)
        self.client = APIClient()

        credentials: str = f"{self.user.email}:test"
        encoded_credentials: str = base64.b64encode(credentials.encode("utf-8")).decode(
            "utf-8"
        )
        self.headers: Dict[str, str] = {
            "HTTP_AUTHORIZATION": f"Basic {encoded_credentials}"
        }

    def test_user_cant_access_swagger_url(self):
        """
        Test if user can access swagger url.
        Expected result: 401 Unauthorized because user is not staff.
        """

        response: Response = self.client.get(self.url, **self.headers)

        self.assertEqual(response.status_code, 401)
        self.assertIsInstance(response.data.get("detail"), ErrorDetail)

    @mute_post_save_signal()
    def test_staff_can_access_swagger_url(self):
        """
        Test if staff can access swagger url.
        Expected result: 200 OK.
        """

        self.user.is_staff = True
        self.user.save()
        response: Response = self.client.get(self.url, **self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, Swagger)
