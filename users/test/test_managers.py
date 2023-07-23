from unittest import mock
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from users.managers import (GoogleManager, GoogleSdkLoginCredentials,
                            SocialAppManager, SocialAppPydantic)
from utils.test.test_utils import ExternalCallsGuardMixin, MockedResponse

User = get_user_model()


@pytest.mark.django_db
class TestGoogleManager(TestCase, ExternalCallsGuardMixin):
    """Test GoogleManager class."""

    @staticmethod
    def patch_social_app_method(instance) -> None:
        """Patch get_social_app method to return specified instance."""
        patch.object(SocialAppManager, "get_social_app", return_value=instance).start()

    def tearDown(self) -> None:
        """Stop all patches."""
        patch.stopall()

    def test_init_method_no_social_app_instance(self) -> None:
        """Test if init method raises exception when credentials not found"""
        with pytest.raises(ImproperlyConfigured) as e:
            GoogleManager()
        assert str(e.value) == "Google provider is missing in DB."

    def test_init_method_no_client_id(self) -> None:
        """Test if init method raises exception when client_id is None"""
        self.patch_social_app_method(
            SocialAppPydantic(client_id=None, client_secret="secret")
        )
        with pytest.raises(ImproperlyConfigured) as e:
            GoogleManager()
        assert str(e.value) == "Google oauth2 client id missing in DB."

    def test_init_method_no_client_secret(self) -> None:
        """Test if init method raises exception when client_secret is None"""
        self.patch_social_app_method(
            SocialAppPydantic(client_id="client+id", client_secret=None)
        )
        with pytest.raises(ImproperlyConfigured) as e:
            GoogleManager()
        assert str(e.value) == "Google oauth2 client secret key missing in DB."

    @override_settings(GOOGLE_OAUTH2_PROJECT_ID=None)
    def test_init_method_no_project_id(self) -> None:
        """Test if init method raises exception when project_id is None"""
        self.patch_social_app_method(
            SocialAppPydantic(client_id="client_id", client_secret="client_secret")
        )
        with pytest.raises(ImproperlyConfigured) as e:
            GoogleManager()
        assert str(e.value) == "Google oauth2 project id missing in settings."

    @override_settings(GOOGLE_OAUTH2_PROJECT_ID="project_id")
    def test_init_method_ok(self) -> None:
        """Test if init method creates instance"""
        self.patch_social_app_method(
            SocialAppPydantic(client_id="client_id", client_secret="client_secret")
        )
        manager = GoogleManager()

        assert isinstance(
            credentials := manager._credentials, GoogleSdkLoginCredentials
        )
        assert credentials.client_id == "client_id"
        assert credentials.client_secret == "client_secret"
        assert credentials.project_id == "project_id"

    def test_get_social_app_called_once(self) -> None:
        """Test if get_social_app method is called once"""
        with patch.object(SocialAppManager, "get_social_app") as mock_method:
            GoogleManager()
        mock_method.assert_called_once_with(provider="google")

    @override_settings(GOOGLE_OAUTH2_PROJECT_ID="project_id")
    def test_get_user_info_value_error(self) -> None:
        """Test if get_user_info method raises ValueError"""
        self.patch_social_app_method(
            SocialAppPydantic(client_id="client_id", client_secret="client_secret")
        )
        mock.patch(
            "users.managers.requests.get",
            return_value=MockedResponse.create(status_code=404),
        ).start()
        with pytest.raises(ValueError):
            GoogleManager().get_user_info(access_token="access_token")

    @override_settings(GOOGLE_OAUTH2_PROJECT_ID="project_id")
    def test_get_user_info_ok(self) -> None:
        """Test if get_user_info method returns valid data"""
        response_data = {"some_response_data": True}
        self.patch_social_app_method(
            SocialAppPydantic(client_id="client_id", client_secret="client_secret")
        )
        mock.patch(
            "users.managers.requests.get",
            return_value=MockedResponse.create(
                status_code=200, json_data=response_data
            ),
        ).start()
        response: dict = GoogleManager().get_user_info(access_token="access_token")

        assert list(response_data.keys())[0] in response
