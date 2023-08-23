from unittest import mock
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from users.schemas import (
    UserGoogleDetailPydantic,
    SocialAppPydantic,
    UserFacebookDetailPydantic,
)
from users.managers import (
    GoogleManager,
    SocialAppManager,
    SocialAuthMixin,
    FacebookManager,
)
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

    def test_google_sdk_login_get_credentials_method_no_social_app_instance(
        self,
    ) -> None:
        """Test if google_sdk_login_get_credentials method raises exception when credentials not found"""
        with pytest.raises(ImproperlyConfigured) as e:
            GoogleManager.google_sdk_login_get_credentials()
        assert str(e.value) == "Google provider is missing in DB."

    def test_google_sdk_login_get_credentials_method_no_client_id(self) -> None:
        """Test if google_sdk_login_get_credentials method raises exception when client_id is None"""
        self.patch_social_app_method(
            SocialAppPydantic(client_id=None, client_secret="secret")
        )
        with pytest.raises(ImproperlyConfigured) as e:
            GoogleManager.google_sdk_login_get_credentials()
        assert str(e.value) == "Google oauth2 client id missing in DB."

    def test_google_sdk_login_get_credentials_method_no_client_secret(self) -> None:
        """Test if google_sdk_login_get_credentials method raises exception when client_secret is None"""
        self.patch_social_app_method(
            SocialAppPydantic(client_id="client+id", client_secret=None)
        )
        with pytest.raises(ImproperlyConfigured) as e:
            GoogleManager.google_sdk_login_get_credentials()
        assert str(e.value) == "Google oauth2 client secret key missing in DB."

    @override_settings(GOOGLE_OAUTH2_PROJECT_ID=None)
    def test_google_sdk_login_get_credentials_method_no_project_id(self) -> None:
        """Test if google_sdk_login_get_credentials method raises exception when project_id is None"""
        self.patch_social_app_method(
            SocialAppPydantic(client_id="client_id", client_secret="client_secret")
        )
        with pytest.raises(ImproperlyConfigured) as e:
            GoogleManager.google_sdk_login_get_credentials()
        assert str(e.value) == "Google oauth2 project id missing in settings."

    def test_get_social_app_called_once(self) -> None:
        """Test if get_social_app method is called once"""
        with patch.object(
            SocialAppManager, "get_social_app", return_value=None
        ) as mock_method:
            try:
                GoogleManager.google_sdk_login_get_credentials()
            except ImproperlyConfigured:
                pass
        mock_method.assert_called_once_with(provider="google")

    @override_settings(GOOGLE_OAUTH2_PROJECT_ID="project_id")
    def test_get_user_info_value_error(self) -> None:
        """Test if get_user_info method raises ValueError"""
        response_mock: MockedResponse = MockedResponse.create(
            status_code=404,
            json_data={"error": "error", "error_description": "error_description"},
        )
        self.patch_social_app_method(
            SocialAppPydantic(client_id="client_id", client_secret="client_secret")
        )
        mock.patch("users.managers.requests.get", return_value=response_mock).start()
        with pytest.raises(ValueError):
            GoogleManager(token_id="token_id").get_user_info()

    @override_settings(GOOGLE_OAUTH2_PROJECT_ID="project_id")
    def test_get_user_info_ok(self) -> None:
        """Test if get_user_info method returns valid data"""
        response_data = {
            "sub": "True",
            "given_name": "True",
            "family_name": "True",
            "email": "True",
        }
        self.patch_social_app_method(
            SocialAppPydantic(client_id="client_id", client_secret="client_secret")
        )
        mock.patch(
            "users.managers.requests.get",
            return_value=MockedResponse.create(
                status_code=200, json_data=response_data
            ),
        ).start()

        response: UserGoogleDetailPydantic = GoogleManager(
            token_id="access_token"
        ).get_user_info()

        assert isinstance(response, UserGoogleDetailPydantic)
        assert list(response_data.keys())[0] in response.dict()

    @override_settings(GOOGLE_OAUTH2_PROJECT_ID="project_id")
    def test_google_response_invalid(self) -> None:
        """Test if google_response method raises ValueError when fetched data is invalid"""
        response_data = {
            "sub": "True",
        }
        self.patch_social_app_method(
            SocialAppPydantic(client_id="client_id", client_secret="client_secret")
        )
        mock.patch(
            "users.managers.requests.get",
            return_value=MockedResponse.create(
                status_code=200, json_data=response_data
            ),
        ).start()
        mock.patch(
            "users.managers.requests.get",
            return_value=MockedResponse.create(
                status_code=200, json_data=response_data
            ),
        ).start()
        with pytest.raises(ValueError):
            GoogleManager(token_id="access_token").get_user_info()


class TestSocialAuthMixin(TestCase, ExternalCallsGuardMixin):
    """Test SocialAuthMixin class."""

    def setUp(self) -> None:
        class TestClass(SocialAuthMixin):
            URL = "some_url"

            def __init__(self, token_id: str):
                self.token_id = token_id

        self.mocked_test_class = TestClass(token_id="token_id")

    def tearDown(self) -> None:
        """Stop all patches."""
        patch.stopall()

    def test_request_user_data_method(self):
        """Test if request_user_data method returns valid data"""
        response_data = {
            "sub": "True",
            "given_name": "True",
            "family_name": "True",
            "email": "True",
        }
        mock.patch(
            "users.managers.requests.get",
            return_value=MockedResponse.create(
                status_code=200, json_data=response_data
            ),
        ).start()
        response: dict = self.mocked_test_class.request_user_data()

        assert isinstance(response, dict)
        assert list(response_data.keys())[0] in response

    def test_request_user_data_method_value_error(self):
        """Test if request_user_data method raises ValueError"""
        response_data = {
            "error": "error",
            "error_description": "error_description",
        }
        mock.patch(
            "users.managers.requests.get",
            return_value=MockedResponse.create(
                status_code=404, json_data=response_data, force_error=True
            ),
        ).start()
        with pytest.raises(ValueError) as err:
            self.mocked_test_class.request_user_data()

        assert "Reason" in str(err.value)
        assert response_data["error_description"] in str(err.value)

    def test_request_user_data_method_no_description_in_error(self):
        """Test if request_user_data method raises ValueError and return error_description"""
        response_data = {
            "error": {"message": "error"},
        }
        mock.patch(
            "users.managers.requests.get",
            return_value=MockedResponse.create(
                status_code=404, json_data=response_data, force_error=True
            ),
        ).start()
        with pytest.raises(ValueError) as err:
            self.mocked_test_class.request_user_data()

        assert "Error. Reason" in str(err.value)


class TestFacebookManager(TestCase, ExternalCallsGuardMixin):
    """Test FacebookManager class."""

    def setUp(self) -> None:
        self.mocked_facebook_manager = FacebookManager(token_id="token_id")

    def test_get_user_info_method(self):
        """Test if get_user_info method returns valid data"""
        response_data = {
            "id": "id",
            "name": "name",
            "email": "email",
        }
        mock.patch(
            "users.managers.SocialAuthMixin.request_user_data",
            return_value=response_data
        ).start()
        response: UserFacebookDetailPydantic = self.mocked_facebook_manager.get_user_info()

        assert isinstance(response, UserFacebookDetailPydantic)
        assert response_data["id"] == response.sub

    def test_get_user_info_method_value_error(self):
        """Test if get_user_info method raises ValueError"""
        response_data = {
            "error": "error",
            "error_description": "error_description",
        }
        mock.patch(
            "users.managers.SocialAuthMixin.request_user_data",
            return_value=response_data
        ).start()

        with pytest.raises(ValueError):
            self.mocked_facebook_manager.get_user_info()

    def test_get_user_info_method_name_has_one_element(self):
        """Test if get_user_info method returns valid data when name has one element"""
        response_data = {
            "id": "id",
            "name": "name",
            "email": "email",
        }
        mock.patch(
            "users.managers.SocialAuthMixin.request_user_data",
            return_value=response_data
        ).start()
        response: UserFacebookDetailPydantic = self.mocked_facebook_manager.get_user_info()

        assert isinstance(response, UserFacebookDetailPydantic)
        assert response_data["id"] == response.sub
        assert response_data["name"] == response.given_name
        assert response_data["name"] == response.family_name
        assert response_data["email"] == response.email
