from typing import Dict, Set, Tuple
from unittest import TestCase
from unittest.mock import patch

import pytest
from allauth.socialaccount.models import SocialAccount
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.test import APIClient, APITestCase

from api.schemas import RegisterSchema
from features.models import Feature
from users.entities import UserGoogleDetailPydantic
from users.managers import GoogleManager, GoogleSdkLoginCredentials
from users.models import User
from users.services import UserService
from utils.factories.feature_sets_factories import (FeatureElementFactory,
                                                    FeatureFactory)
from utils.factories.user_factories import UserFactory
from utils.test.test_utils import (TEST_EMAIL, MethodsNotAllowedTestsMixin,
                                   UserManager, mute_post_save_signal)


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
            "email": TEST_EMAIL,
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


@pytest.mark.django_db
class TestUserFeatureSetsEndpoint(TestCase, MethodsNotAllowedTestsMixin):
    NOT_ALLOWED_METHODS = ["post", "put", "patch", "delete"]

    def setUp(self) -> None:
        """Setup method for UserFeatureSetsEndpoint tests"""
        self.client: APIClient = APIClient()
        user_manager: UserManager = UserManager(self.client)
        self.user: User = user_manager.create_superuser()
        self.headers: dict = user_manager.get_headers()
        self.url: str = reverse("api:users:feature-sets")

    def test_unauthorized_user(self) -> None:
        """Test if only authenticated user can access endpoint"""
        res: Response = self.client.get(self.url)
        assert res.status_code == 401

    def test_method_get_ok(self) -> None:
        """Test if response is OK"""
        feature_set: Feature = FeatureFactory.create()

        expected_access = {
            "role": feature_set.elements.first().access_permissions.first().role,
            "access": feature_set.elements.first().access_permissions.first().access,
        }
        feature_elements = {
            "name": feature_set.elements.first().name,
            "access_permissions": [expected_access],
            "permissions": feature_set.elements.first().permissions,
        }
        expected_response = [
            {
                "name": feature_set.name,
                "keyname": feature_set.keyname,
                "enabled": feature_set.enabled,
                "elements": [feature_elements],
            }
        ]
        res: Response = self.client.get(self.url, **self.headers)

        assert res.status_code == 200
        assert res.json() == expected_response

    def test_no_feature_sets_found(self):
        """Test if response is 404 when no feature sets are found"""
        res: Response = self.client.get(self.url, **self.headers)
        assert res.status_code == 404


@pytest.mark.django_db
class TestUserFeatureElementsEndpoint(TestCase, MethodsNotAllowedTestsMixin):
    NOT_ALLOWED_METHODS = ["post", "put", "patch", "delete"]

    def setUp(self) -> None:
        """Setup method for UserFeatureElementsEndpoint tests"""
        self.client: APIClient = APIClient()
        user_manager: UserManager = UserManager(self.client)
        self.user: User = user_manager.create_superuser()
        self.headers = user_manager.get_headers()
        self.url: str = reverse("api:users:feature-elements")

    def test_unauthorized_user(self) -> None:
        """Test if only authenticated user can access endpoint"""
        res: Response = self.client.get(self.url)
        assert res.status_code == 401

    def test_method_get_ok(self) -> None:
        """Test if response is OK"""
        feature_element = FeatureElementFactory.create()

        expected_access = {
            "role": feature_element.access_permissions.first().role,
            "access": feature_element.access_permissions.first().access,
        }
        feature_elements = {
            "name": feature_element.name,
            "access_permissions": [expected_access],
            "permissions": feature_element.permissions,
        }
        expected_response = [feature_elements]
        res: Response = self.client.get(self.url, **self.headers)

        assert res.status_code == 200
        assert res.json() == expected_response

    def test_no_feature_elements_found(self):
        """Test if response is 404 when no feature elements are found"""
        res: Response = self.client.get(self.url, **self.headers)
        assert res.status_code == 404


@pytest.mark.django_db
class GoogleAuthTestEndpoint(TestCase, MethodsNotAllowedTestsMixin):
    """Integration tests for google-oauth2 endpoint"""

    NOT_ALLOWED_METHODS = ["get", "put", "patch", "delete"]

    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.url: str = reverse("api:users:google-oauth2")
        self.unregistered_user_data: dict = {
            "email": TEST_EMAIL,
            "token_id": "example_token_id",
        }

    def tearDown(self) -> None:
        """Stop all patches."""
        patch.stopall()

    @mute_post_save_signal()
    def test_endpoint_ok(self) -> None:
        """
        Test if response is OK. User doesn't exist in db,
        so the response should include a register value
        """
        user_email: str = self.unregistered_user_data.get("email")

        expected_res = {
            "success": True,
            "redirect": "register",
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
        }
        user_info_mock = {
            "sub": "106746665020843434121824568902",
            "name": "Test User",
            "given_name": "Test",
            "family_name": "User",
            "picture": "example_url",
            "email": user_email,
            "email_verified": True,
            "locale": "pl",
        }
        google_auth_credentials_mock = GoogleSdkLoginCredentials(
            client_id="client_id",
            client_secret="client_secret",
            project_id="project_id",
        )
        google_credentials_patcher = patch.object(
            GoogleManager,
            "google_sdk_login_get_credentials",
            return_value=google_auth_credentials_mock,
        )
        get_user_info_patcher = patch.object(
            GoogleManager,
            "get_user_info",
            return_value=UserGoogleDetailPydantic(**user_info_mock),
        )
        social_account = SocialAccount.objects.filter(user__email=user_email)

        assert not social_account.exists()

        with get_user_info_patcher, google_credentials_patcher:
            res: Response = self.client.post(  # type: ignore
                self.url, data=self.unregistered_user_data
            )

            data: dict = res.json()  # type: ignore

            assert res.status_code == 200

            for elements in expected_res.keys():
                assert elements in data

            assert data.get("redirect") == expected_res.get("redirect")
            assert data.get("success") == expected_res.get("success")

            user_qry = User.objects.filter(email=user_email)

            assert user_qry.exists()
            assert isinstance(user := user_qry.first(), User)
            assert user.email == user_email

            assert social_account.exists()

    def test_no_token_sent(self) -> None:
        """Test if response is 400 when no token is sent"""
        res: Response = self.client.post(self.url, data={})
        assert res.status_code == 400


@pytest.mark.django_db
class GoogleAuthUnitTestsEndpoint(TestCase, MethodsNotAllowedTestsMixin):
    """Unit tests for google-oauth2 endpoint"""

    NOT_ALLOWED_METHODS = ["get", "put", "patch", "delete"]

    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.url: str = reverse("api:users:google-oauth2")
        self.unregistered_user_data: dict = {
            "email": TEST_EMAIL,
            "token_id": "example_token_id",
        }
        self.user_info_mock: dict = {
            "sub": "106746665020843434121824568902",
            "name": "Test User",
            "given_name": "Test",
            "family_name": "User",
            "picture": "example_url",
            "email": "example_email",
            "email_verified": True,
            "locale": "pl",
        }

    def tearDown(self):
        patch.stopall()

    def patch_methods(self) -> Tuple[patch, patch, patch]:
        """
        Helper method to patch specific methods:
        get_user_info, google_sdk_login_get_credentials, register_from_google
        """

        google_auth_credentials_mock = GoogleSdkLoginCredentials(
            client_id="client_id",
            client_secret="client_secret",
            project_id="project_id",
        )
        get_user_info_patcher = patch.object(
            GoogleManager,
            "get_user_info",
            return_value=UserGoogleDetailPydantic(**self.user_info_mock),
        )
        google_credentials_patcher = patch.object(
            GoogleManager,
            "google_sdk_login_get_credentials",
            return_value=google_auth_credentials_mock,
        )
        register_from_google_patcher = patch.object(
            UserService, "register_from_google", return_value=UserFactory.create()
        )

        return (
            google_credentials_patcher,
            get_user_info_patcher,
            register_from_google_patcher,
        )

    def test_google_manager_improperly_configured_exception(self) -> None:
        """Test if response is 400 when ImproperlyConfigured exception is raised"""
        google_credentials_patcher = patch.object(
            GoogleManager,
            "google_sdk_login_get_credentials",
            side_effect=ImproperlyConfigured(),
        )

        with google_credentials_patcher:
            res: Response = self.client.post(  # type: ignore
                self.url, data=self.unregistered_user_data
            )
            assert res.status_code == 400
            assert res.json().get("detail") == "Failed to obtain Google credentials."

    def test_google_manager_value_exception(self) -> None:
        """Test if response is 400 when ValueError exception is raised"""
        google_credentials_patcher = patch.object(
            GoogleManager, "google_sdk_login_get_credentials", side_effect=ValueError()
        )

        with google_credentials_patcher:
            res: Response = self.client.post(  # type: ignore
                self.url, data=self.unregistered_user_data
            )
            assert res.status_code == 400

    def test_response_ok_register_page(self) -> None:
        """
        Test if response is OK. User doesn't exist in db,
        so the response should include a register value
        """

        (
            get_user_info_patcher,
            google_credentials_patcher,
            register_from_google_patcher,
        ) = self.patch_methods()
        patch.object(
            UserService, "create_social_account", return_value=(True, True)
        ).start()

        with get_user_info_patcher, google_credentials_patcher, register_from_google_patcher:
            res: Response = self.client.post(  # type: ignore
                self.url, data=self.unregistered_user_data
            )
            assert res.status_code == 200
            assert res.json().get("redirect") == "register"
            assert res.json().get("success") is True

    def test_response_ok_landing_page(self) -> None:
        """
        Test if response is OK.
        User exists in db, so the response should include a landing page value
        """

        UserFactory.create(email=self.user_info_mock.get("email"))
        (
            get_user_info_patcher,
            google_credentials_patcher,
            register_from_google_patcher,
        ) = self.patch_methods()
        patch.object(
            UserService, "create_social_account", return_value=(True, True)
        ).start()

        with get_user_info_patcher, google_credentials_patcher, register_from_google_patcher:
            res: Response = self.client.post(  # type: ignore
                self.url, data=self.unregistered_user_data
            )
            assert res.status_code == 200
            assert res.json().get("redirect") == "landing page"
            assert res.json().get("success") is True

    def test_response_no_user_credentials_exception(self) -> None:
        """Test if response is 400 when no data is fetched from Google"""

        UserFactory.create(email=self.user_info_mock.get("email"))
        (
            get_user_info_patcher,
            google_credentials_patcher,
            register_from_google_patcher,
        ) = self.patch_methods()
        patch.object(
            UserService, "create_social_account", return_value=(False, True)
        ).start()
        with get_user_info_patcher, google_credentials_patcher, register_from_google_patcher:
            res: Response = self.client.post(  # type: ignore
                self.url, data=self.unregistered_user_data
            )
            assert res.status_code == 400

            msg = "No user data fetched from Google or data is not valid. Please try again."
            assert res.json().get("detail") == msg
