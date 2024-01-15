import json

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.test import APIClient, APITestCase

from features.models import NewFeatureSubscription
from utils.test.test_utils import MethodsNotAllowedTestsMixin, UserManager

User = get_user_model()


class TestUserCreationEndpoint(APITestCase, MethodsNotAllowedTestsMixin):
    NOT_ALLOWED_METHODS = ["get", "put", "patch", "delete"]
    headers = {}

    def setUp(self) -> None:
        self.client = APIClient()
        self.url = reverse("api:features:create_feature_subscription_entity")
        user_manager: UserManager = UserManager(self.client)
        self.user: User = user_manager.create_superuser()
        self.headers: dict = user_manager.get_headers()
        self.data = {"name": "test_feature", "category": "player base"}

    @pytest.mark.usefixtures("disable_throttle_for_feature_notification_test")
    def test_request_methods_not_allowed(self) -> None:
        """Disable throttle for test_request_methods_not_allowed tests"""
        super().test_request_methods_not_allowed()

    def test_create_feature_subscription_entity_no_auth(self) -> None:
        """Test endpoint without authentication"""

        res = self.client.post(self.url)
        assert res.status_code == 401

    def test_create_feature_subscription_entity_no_data(self) -> None:
        """Test endpoint with authentication but no data sent"""

        res = self.client.post(self.url, **self.headers)
        assert res.status_code == 400

        for element in ["name", "category"]:
            assert element in res.data

    def test_create_feature_subscription_entity(self) -> None:
        """Test endpoint with authentication"""

        res = self.client.post(self.url, data=json.dumps(self.data), **self.headers)
        assert res.status_code == 201

        feature_obj: NewFeatureSubscription = NewFeatureSubscription.objects.first()
        assert feature_obj.name == self.data["name"]
        assert feature_obj.category == self.data["category"]

    def test_throttle(self) -> None:
        """Check if throttle works properly"""
        res = self.client.post(self.url, data=json.dumps(self.data), **self.headers)
        assert res.status_code == 201

        for _ in range(2):
            res: Response = self.client.post(
                self.url,
                data=self.data,
            )

            assert res.status_code != 429
