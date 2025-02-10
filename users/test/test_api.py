from typing import Dict, Tuple
from unittest import TestCase
from unittest.mock import patch

import pytest
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.contrib.auth import authenticate
from django.core import mail
from django.core.cache import cache
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.test import APIClient, APITestCase

from features.models import Feature
from users.api.views import UsersAPI
from users.errors import (
    ApplicationError,
    SocialAccountInstanceNotCreatedException,
    UserEmailNotValidException,
)
from users.managers import FacebookManager, GoogleManager
from users.models import Ref, User
from users.schemas import (
    GoogleSdkLoginCredentials,
    LoginSchemaOut,
    RegisterSchema,
    UserFacebookDetailPydantic,
    UserGoogleDetailPydantic,
)
from users.services import UserService
from users.utils.test_utils import extract_uidb64_and_token_from_email
from utils.factories.feature_sets_factories import FeatureElementFactory, FeatureFactory
from utils.factories.user_factories import UserFactory
from utils.test.test_utils import (
    TEST_EMAIL,
    MethodsNotAllowedTestsMixin,
    UserManager,
    mute_post_save_signal,
)


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

    def test_login_response_schema(self):
        """Test if login response schema is correct"""
        res: Response = self.login()
        for element in LoginSchemaOut.__fields__.keys():
            assert element in res.data


@pytest.mark.django_db
class TestUserCreationEndpoint(TestCase, MethodsNotAllowedTestsMixin):
    NOT_ALLOWED_METHODS = ["get", "put", "patch", "delete"]

    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.url: str = reverse("api:users:api-register")
        self.data: Dict[str, str] = {
            "password": "super secret password",
            "first_name": "first_name",
            "last_name": "last_name",
            "email": TEST_EMAIL,
        }

    def tearDown(self) -> None:
        """Stop all patches and clear throttle cache"""
        patch.stopall()
        cache.clear()

    @pytest.mark.usefixtures("disable_email_check_throttle_for_test")
    def test_request_methods_not_allowed(self) -> None:
        """Disable throttle for test_request_methods_not_allowed tests"""
        super().test_request_methods_not_allowed()

    def test_throttle(self) -> None:
        """Check if throttle works properly"""

        for _ in range(settings.THROTTLE_EMAIL_CHECK_LIMITATION):
            res: Response = self.client.post(
                self.url,
                data=self.data,
            )

            assert res.status_code != 429

        res: Response = self.client.post(
            self.url,
            data=self.data,
        )
        assert res.status_code == 429

    @mute_post_save_signal()
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

    def test_register_ref_uuid_created(self) -> None:
        """Test register endpoint. Response OK"""

        res: Response = self.client.post(
            self.url,
            data=self.data,
        )

        assert res.status_code == 200
        assert User.objects.get(pk=res.data["id"]).ref

    def test_register_with_ref_uuid(self) -> None:
        """Test register endpoint. Response OK"""
        user_ref = Ref.objects.create(user=UserFactory())
        self.client.cookies["referral_code"] = str(user_ref.uuid)
        res: Response = self.client.post(
            self.url,
            data=self.data,
        )

        assert res.status_code == 200
        assert user_ref.referrals.first().user.pk == res.data["id"]

    def test_register_endpoint_no_password_sent(self) -> None:
        """Test register endpoint with no password field"""

        self.data.pop("password")
        res: Response = self.client.post(
            self.url,
            data=self.data,
        )

        assert res.status_code == 400
        assert isinstance(res.data, dict)
        assert res.data["detail"]
        assert isinstance(res.data["fields"], dict)
        assert "password" in res.data["fields"]

    def test_register_endpoint_no_email(self) -> None:
        """Test register endpoint with no email field"""

        self.data.pop("email")
        res: Response = self.client.post(
            self.url,
            data=self.data,
        )

        assert res.status_code == 400
        assert isinstance(res.data, dict)
        assert res.data["detail"]
        assert isinstance(res.data["fields"], dict)
        assert "email" in res.data["fields"]

    def test_register_endpoint_invalid_mail(self) -> None:
        """Test register endpoint with invalid email field"""

        invalid_names = [
            "test_email",
            "test_email@",
            "test_email@test",
            "test_email@test.",
        ]

        for email in invalid_names:
            self.data["email"] = email
            res: Response = self.client.post(
                self.url,
                data=self.data,
            )

            assert res.status_code == 400
            data: dict = res.json()  # type: ignore

            assert data.get("success") == "False"
            assert isinstance(data.get("fields"), dict)
            assert "email" in data.get("fields")

    @mute_post_save_signal()
    def test_password_not_returned(self) -> None:
        """Test if password field is not returned"""

        res: Response = self.client.post(
            self.url,
            data=self.data,
        )

        assert "password" not in res.data

    def test_user_already_exists(self) -> None:
        """Test if user can register account for the second time using the same email"""

        self.client.post(self.url, data=self.data)

        res: Response = self.client.post(
            self.url,
            data=self.data,
        )
        data: dict = res.json()  # type: ignore

        assert res.status_code == 400
        assert data.get("success") == "False"
        assert isinstance(data.get("fields"), dict)
        assert "email" in data.get("fields")

    def test_response_data(self) -> None:
        """Test if response data contains all required fields from RegisterSchema"""

        user_schema: RegisterSchema = RegisterSchema(**self.data)  # type: ignore
        fields: dict = user_schema.dict(exclude={"password"})
        res: Response = self.client.post(self.url, data=self.data)

        for field in fields:
            assert field in res.data

    def test_user_creation_without_first_name(self):
        """Test if user can be created without first_name"""
        self.data.pop("first_name")

        res: Response = self.client.post(self.url, data=self.data)

        assert res.status_code == 200
        assert isinstance(res.data, dict)
        assert res.data["email"] == self.data.get("email")
        assert res.data["id"]
        assert res.data["username"] == self.data.get("email")
        assert not res.data["first_name"]

    def test_user_creation_without_last_name(self):
        """Test if user can be created without last_name"""
        self.data.pop("last_name")

        res: Response = self.client.post(self.url, data=self.data)

        assert res.status_code == 200
        assert isinstance(res.data, dict)
        assert res.data["email"] == self.data.get("email")
        assert res.data["id"]
        assert res.data["username"] == self.data.get("email")
        assert not res.data["last_name"]

    def test_user_creation_without_last_name_and_first_name(self):
        """Test if user can be created without last_name and first_name"""
        self.data.pop("last_name")
        self.data.pop("first_name")

        res: Response = self.client.post(self.url, data=self.data)

        assert res.status_code == 200
        assert isinstance(res.data, dict)
        assert res.data["email"] == self.data.get("email")
        assert res.data["id"]
        assert res.data["username"] == self.data.get("email")
        assert not res.data["last_name"]
        assert not res.data["first_name"]

    def test_user_creation_password_too_short(self):
        """Test if user can be created with too short password"""
        self.data["password"] = "123"

        res: Response = self.client.post(self.url, data=self.data)

        assert res.status_code == 400
        assert isinstance(res.data, dict)
        assert res.data["detail"]
        assert isinstance(res.data["fields"], dict)
        assert "password" in res.data["fields"]


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
        """Test if response is 204 when no feature sets are found"""
        res: Response = self.client.get(self.url, **self.headers)
        assert res.status_code == 204
        assert res.data == []


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
        """Test if response is 204 when no feature elements are found"""
        res: Response = self.client.get(self.url, **self.headers)
        assert res.status_code == 204


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
        expected_res, user_info_mock = self.expected_res_user_info()
        get_user_info_patcher, google_credentials_patcher = self.mock_objects(
            user_info_mock=user_info_mock
        )
        expected_res["last_name"] = "User"
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
            assert data.get("access_token") is not None
            assert data.get("refresh_token") is not None
            assert data.get("first_name") == expected_res.get("first_name")
            assert data.get("last_name") == expected_res.get("last_name")
            assert len(data) == len(expected_res)

            user_qry = User.objects.filter(email=user_email)

            assert user_qry.exists()
            assert isinstance(user := user_qry.first(), User)  # noqa: E999
            assert user.email == user_email

            assert social_account.exists()

    def expected_res_user_info(self) -> Tuple[dict, dict]:
        """Prepare expected response and user info mock"""
        user_email: str = self.unregistered_user_data.get("email")
        expected_res = {
            "success": True,
            "redirect": "register",
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "first_name": "Test",
            "last_name": "User",
            "id": 2137,
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

        return expected_res, user_info_mock

    def mock_objects(self, user_info_mock: dict) -> Tuple[patch, patch]:
        """Mock objects for tests"""
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
        return get_user_info_patcher, google_credentials_patcher

    @mute_post_save_signal()
    def test_endpoint_ok_no_last_name(self) -> None:
        """
        Test if response is OK. User doesn't exist in db,
        so the response should include a register value.
        Google don't return last_name.
        """
        user_email: str = self.unregistered_user_data.get("email")
        expected_res, user_info_mock = self.expected_res_user_info()
        expected_res["last_name"] = None
        user_info_mock.pop("family_name")
        get_user_info_patcher, google_credentials_patcher = self.mock_objects(
            user_info_mock=user_info_mock
        )

        with get_user_info_patcher, google_credentials_patcher:
            res: Response = self.client.post(self.url, data=self.unregistered_user_data)

            data: dict = res.json()  # type: ignore

            assert res.status_code == 200

            for elements in expected_res.keys():
                assert elements in data

            assert data.get("redirect") == expected_res.get("redirect")
            assert data.get("success") == expected_res.get("success")
            assert data.get("access_token") is not None
            assert data.get("refresh_token") is not None
            assert data.get("first_name") == expected_res.get("first_name")
            assert data.get("last_name") == expected_res.get("last_name")
            assert len(data) == len(expected_res)

            user_qry = User.objects.filter(email=user_email)

            assert user_qry.exists()
            assert isinstance(user := user_qry.first(), User)  # noqa: E999
            assert user.email == user_email

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
        self.expected_res = {
            "success": True,
            "redirect": "register",
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "first_name": "Test",
            "last_name": "User",
            "id": 321,
        }
        self.user_patcher = UserFactory.create(
            first_name=self.user_info_mock["given_name"],
            last_name=self.user_info_mock["family_name"],
        )

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
            UserService, "register_from_social", return_value=self.user_patcher
        )

        return (
            get_user_info_patcher,
            google_credentials_patcher,
            register_from_google_patcher,
        )

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

        with (
            get_user_info_patcher
        ), google_credentials_patcher, register_from_google_patcher:
            res: Response = self.client.post(  # type: ignore
                self.url, data=self.unregistered_user_data
            )
            assert res.status_code == 200

            for element in self.expected_res.keys():
                assert element in res.json()

            assert len(res.json()) == len(self.expected_res)

            assert res.json().get("redirect") == "register"
            assert res.json().get("success") is True
            assert res.json().get("access_token") is not None
            assert res.json().get("refresh_token") is not None
            assert res.json().get("first_name") == self.user_patcher.first_name
            assert res.json().get("last_name") == self.user_patcher.last_name

    def test_response_ok_landing_page(self) -> None:
        """
        Test if response is OK.
        User exists in db, so the response should include a landing page value
        """

        user: User = UserFactory.create(email=self.user_info_mock.get("email"))
        (
            get_user_info_patcher,
            google_credentials_patcher,
            register_from_google_patcher,
        ) = self.patch_methods()
        patch.object(
            UserService, "create_social_account", return_value=(True, True)
        ).start()

        with (
            get_user_info_patcher
        ), google_credentials_patcher, register_from_google_patcher:
            res: Response = self.client.post(  # type: ignore
                self.url, data=self.unregistered_user_data
            )

            assert res.status_code == 200
            assert res.json().get("redirect") == "landing page"
            assert res.json().get("success") is True
            assert res.json().get("access_token") is not None
            assert res.json().get("refresh_token") is not None
            assert res.json().get("first_name") == user.first_name
            assert res.json().get("last_name") == user.last_name

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
        with (
            get_user_info_patcher
        ), google_credentials_patcher, register_from_google_patcher:
            res: Response = self.client.post(  # type: ignore
                self.url, data=self.unregistered_user_data
            )
            assert res.status_code == 400

            msg = "No user data fetched from Google or data is not valid. Please try again."  # noqa: E501
            assert res.json().get("detail") == msg


@pytest.mark.django_db
class TestEmailAvailabilityEndpoint(TestCase, MethodsNotAllowedTestsMixin):
    NOT_ALLOWED_METHODS = ["get", "put", "patch", "delete"]

    def setUp(self) -> None:
        """Setup method for UserFeatureElementsEndpoint tests"""
        self.client: APIClient = APIClient()
        self.url: str = reverse("api:users:email-verification")
        self.test_email = TEST_EMAIL

    def tearDown(self) -> None:
        """Stop all patches and clear throttle cache"""
        patch.stopall()
        cache.clear()

    @pytest.mark.usefixtures("disable_email_check_throttle_for_test")
    def test_request_methods_not_allowed(self) -> None:
        """Disable throttle for test_request_methods_not_allowed tests"""
        super().test_request_methods_not_allowed()

    def test_throttle(self) -> None:
        """Check if throttle works properly"""

        for _ in range(settings.THROTTLE_EMAIL_CHECK_LIMITATION):
            res: Response = self.client.post(self.url, data={"email": self.test_email})
            assert res.status_code == 200
            assert res.json()["success"] is True

        res: Response = self.client.post(self.url, data={"email": self.test_email})
        assert res.status_code == 429

    @pytest.mark.usefixtures("disable_email_check_throttle_for_test")
    def test_if_email_has_valid_format(self) -> None:
        """Test if email has valid format"""
        data = {"email": "test_email"}
        res: Response = self.client.post(self.url, data=data)

        assert res.status_code == 400
        assert "success" in res.json()
        assert "detail" in res.json()

    @pytest.mark.usefixtures("disable_email_check_throttle_for_test")
    def test_email_is_available(self):
        """Test if email is available"""
        data = {"email": "test@email.com"}
        res: Response = self.client.post(self.url, data=data)

        assert res.status_code == 200
        assert "success" in res.json()
        assert "email_available" in res.json()
        assert res.json()["email_available"] is True
        assert res.json()["success"] is True

    @pytest.mark.usefixtures("disable_email_check_throttle_for_test")
    def test_email_is_not_available(self):
        """Test if email is not available"""
        UserFactory.create(email=self.test_email)
        data = {"email": self.test_email}
        res: Response = self.client.post(self.url, data=data)

        assert res.status_code == 400
        assert "success" in (data := res.json())
        assert data["success"] == "False"
        assert "email_available" not in data
        assert "detail" in data


@pytest.mark.django_db
class TestFacebookAuthEndpoint(TestCase, MethodsNotAllowedTestsMixin):
    NOT_ALLOWED_METHODS = ["get", "put", "patch", "delete"]

    def setUp(self) -> None:
        self.url = reverse("api:users:facebook-auth")
        self.client: APIClient = APIClient()

    def tearDown(self) -> None:
        """Stop all patches."""
        patch.stopall()

    def test_facebook_auth_raises_error(self):
        response: Response = self.client.post(self.url)
        assert response.status_code == 400
        assert "No Social token sent." in response.json()["detail"]

    def test_facebook_auth_response_ok(self):
        response_dict = {
            "success": True,
            "redirect": "landing_page",
            "refresh_token": "some_token",
            "access_token": "some_access_token",
        }

        patch(
            "users.api.views.UsersAPI._social_media_auth", return_value=response_dict
        ).start()
        response: Response = self.client.post(self.url, data={"token_id": "test"})

        assert response.status_code == 200
        assert "success" in response.json()
        assert response.json()["success"] is True
        assert "redirect" in response.json()
        assert response.json()["redirect"] == response_dict["redirect"]


@pytest.mark.django_db
class TestSocialMediaAuthMethod(TestCase):
    def tearDown(self) -> None:
        """Stop all patches."""
        patch.stopall()

    def test__social_media_auth_raises_error(self):
        get_user_info_patcher = patch.object(
            FacebookManager, "get_user_info", side_effect=ValueError()
        )

        with get_user_info_patcher, pytest.raises(ApplicationError):
            UsersAPI._social_media_auth(FacebookManager(token_id="token_id"), "test")

    def test__social_media_auth_ok(self):
        data_patcher = {
            "id": "123456789012345678901",
            "given_name": "Test",
            "family_name": "Test",
            "email": TEST_EMAIL,
        }
        patch(
            "users.managers.FacebookManager.get_user_info",
            return_value=UserFacebookDetailPydantic(**data_patcher),
        ).start()
        patch(
            "users.services.UserService.create_social_account",
            return_value=(True, True),
        ).start()

        res: dict = UsersAPI._social_media_auth(
            FacebookManager(token_id="token_id"), "test"
        )

        assert User.objects.filter(email=data_patcher["email"]).exists()
        assert isinstance(res, dict)
        assert "success" in res
        assert res["redirect"] == "register"
        assert "access_token" in res

    def test__social_media_auth_mail_not_valid(self):
        """Test method _social_media_auth when email is not valid"""
        data_patcher = {
            "id": "123456789012345678901",
            "given_name": "Test",
            "family_name": "Test",
            "email": "TEST_EMAIL",
        }
        patch(
            "users.managers.FacebookManager.get_user_info",
            return_value=UserFacebookDetailPydantic(**data_patcher),
        ).start()
        patch(
            "users.services.UserService.create_social_account",
            return_value=(True, True),
        ).start()

        with pytest.raises(UserEmailNotValidException):
            UsersAPI._social_media_auth(FacebookManager(token_id="token_id"), "test")

    def test__social_media_auth_no_social_acc_created(self):
        """Test method _social_media_auth when no social account is created"""
        data_patcher = {
            "id": "123456789012345678901",
            "given_name": "Test",
            "family_name": "Test",
            "email": TEST_EMAIL,
        }
        patch(
            "users.managers.FacebookManager.get_user_info",
            return_value=UserFacebookDetailPydantic(**data_patcher),
        ).start()
        patch(
            "users.services.UserService.create_social_account",
            return_value=(False, True),
        ).start()

        with pytest.raises(SocialAccountInstanceNotCreatedException):
            UsersAPI._social_media_auth(FacebookManager(token_id="token_id"), "test")


@pytest.mark.django_db
class TestPasswordResetEndpoint(TestCase, MethodsNotAllowedTestsMixin):
    NOT_ALLOWED_METHODS = ["get", "put", "patch", "delete"]

    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.url: str = reverse("api:users:api-password-reset")
        self.user_data: Dict[str, str] = {
            "password": "old_secret_password",
            "first_name": "first_name",
            "last_name": "last_name",
            "email": TEST_EMAIL,
        }
        self.user = UserFactory.create(**self.user_data)

    def test_password_reset_request(self) -> None:
        """Test if reset request returns 200 for valid email."""
        res: Response = self.client.post(
            self.url, data={"email": self.user_data["email"]}
        )
        assert res.status_code == 200

    def test_password_reset_for_non_existent_email(self) -> None:
        """Test if reset request returns a specific status (e.g., 200) for non-existent email."""  # noqa: E501
        res: Response = self.client.post(
            self.url, data={"email": "non_existent@test.com"}
        )
        assert res.status_code == 200

    def test_reset_email_content(self) -> None:
        """Test if the reset email contains the correct content and link."""
        self.client.post(self.url, data={"email": self.user_data["email"]})

        assert len(mail.outbox) == 1
        email = mail.outbox[0]

        # assert email.subject == "Password reset"
        assert email.to == [self.user_data["email"]]
        # assert "Witaj na platformie PlayMaker.pro" in email.body
        # Email subject/body are now dynamicaly generated, so we can't test it


@pytest.mark.django_db
class TestPasswordChangeEndpoint(TestCase, MethodsNotAllowedTestsMixin):
    NOT_ALLOWED_METHODS = ["get", "put", "patch", "delete"]

    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.user_data: Dict[str, str] = {
            "password": "old_secret_password",
            "first_name": "first_name",
            "last_name": "last_name",
            "email": TEST_EMAIL,
        }
        self.user = UserFactory.create(**self.user_data)

        # The URL for the password reset confirmation with dummy args
        # Used for MethodsNotAllowedTestsMixin
        self.url = reverse(
            "api:users:api-password-reset-confirm", args=["dummy_uidb64", "dummy_token"]
        )

        # The URL for initiating the password reset process
        self.initiate_reset_url = reverse("api:users:api-password-reset")

    def test_password_change_with_valid_token(self) -> None:
        """Test if the user can reset their password with a valid token."""

        # Request a password reset
        self.client.post(
            self.initiate_reset_url, data={"email": self.user_data["email"]}
        )
        email = mail.outbox[0]
        uidb64, token = extract_uidb64_and_token_from_email(email.body)

        # Use these values to reverse the change password URL
        change_password_url = reverse(
            "api:users:api-password-reset-confirm", args=[uidb64, token]
        )

        # Perform the password change request using the valid token.
        new_password = "newSecurePassword123!"
        response = self.client.post(
            change_password_url,
            data={"new_password": new_password, "confirm_new_password": new_password},
        )

        # Assert that the password was changed successfully.
        assert response.status_code == 200

        user = User.objects.get(email=self.user_data["email"])
        assert user.check_password(new_password) is True

    def test_password_change_with_invalid_token(self) -> None:
        """Test if the user cannot reset their password with an invalid token."""

        # Make a reset password request. This will generate a valid token.
        self.client.post(
            self.initiate_reset_url, data={"email": self.user_data["email"]}
        )
        email_content = mail.outbox[0].body

        # Extract the real uidb64 and token for the user.
        uidb64, valid_token = extract_uidb64_and_token_from_email(email_content)

        # Intentionally modify the token to make it invalid.
        invalid_token = "invalid-token"
        assert (
            invalid_token != valid_token
        )  # Just to make sure we aren't coincidentally using a valid token.

        # Construct the password reset confirm URL with the invalid token.
        change_password_url_with_invalid_token = reverse(
            "api:users:api-password-reset-confirm", args=[uidb64, invalid_token]
        )

        # Try to reset the password with the invalid token.
        response = self.client.post(
            change_password_url_with_invalid_token,
            data={
                "password": self.user_data["password"],
                "new_password": "newpassword1234",
                "confirm_new_password": "newpassword1234",
            },
        )

        # Check that the response indicates a failure
        assert response.status_code == 400
        user = authenticate(
            email=self.user_data["email"], password=self.user_data["password"]
        )
        assert (
            user is not None
        )  # The authentication should succeed with the old password.
        user = authenticate(username=self.user_data["email"], password="newpassword123")
        assert (
            user is None
        )  # The authentication should fail since the password was not changed.


class TestUserManagementAPI(APITestCase):
    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.manager = UserManager(self.client)
        self.user_obj = self.manager.create_superuser()
        # self.headers = self.manager.get_headers()
        self.image_headers = {
            "HTTP_AUTHORIZATION": f"Bearer {self.manager.get_access_token}",
            "Content-type": "image/jpeg",
        }
        self.picture_url = reverse("api:users:update_profile_picture")

    def test_valid_picture_update(self) -> None:
        """Test update image with valid image (<2MB)"""
        with open("utils/assets/valid_alpaca_image_lt_2MB.jpg", "rb") as image:
            data = {"picture": image}
            res: Response = self.client.post(
                self.picture_url, data=data, **self.image_headers
            )

            assert res.status_code == 200
            assert res.data["picture"] is not None

    def test_too_big_picture_update(self) -> None:
        """Test update image with invalid image (>2MB)"""
        with open("utils/assets/too_big_alpaca_image_gt_2MB.jpg", "rb") as image:
            data = {"picture": image}
            res: Response = self.client.post(
                self.picture_url, data=data, **self.image_headers
            )

            assert res.status_code == 400

    def test_not_allowed_formats_update(self) -> None:
        """Test update image with invalid image (>2MB)"""
        with open("utils/assets/alpaca_gif_not_allowed.gif", "rb") as image:
            data = {"picture": image}
            res: Response = self.client.post(
                self.picture_url, data=data, **self.image_headers
            )

            assert res.status_code == 400

    def test_throttle_picture_update(self) -> None:
        """Test throttling on picture update"""
        with open("utils/assets/valid_alpaca_image_lt_2MB.jpg", "rb") as image:
            data = {"picture": image}
            for _ in range(settings.DEFAULT_THROTTLE):
                self.client.post(self.picture_url, data=data, **self.image_headers)

            res: Response = self.client.post(
                self.picture_url, data=data, **self.image_headers
            )
            assert res.status_code == 429


@pytest.mark.django_db
class TestEmailVerificationEndpoint(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.register_url = reverse("api:users:api-register")
        self.user_data = {
            "password": "super secret password",
            "first_name": "first_name",
            "last_name": "last_name",
            "email": "testuser@example.com",
        }
        self.verify_email_base_url = reverse(
            "api:users:verify_email", args=["dummy_uidb64", "dummy_token"]
        )

    def test_email_verification_process(self) -> None:
        """
        Tests the email verification process for a registered user.
        """
        # Simulate user registration
        self.client.post(self.register_url, data=self.user_data)

        # Extract verification URL from the email
        email = mail.outbox[0]
        uidb64, token = extract_uidb64_and_token_from_email(email.body)
        # Construct the complete verification URL
        verification_url = reverse("api:users:verify_email", args=[uidb64, token])

        # Simulate clicking the verification link
        response = self.client.get(verification_url)
        assert response.status_code == 200

        # Fetch the user and check if the email is verified
        user = User.objects.get(email=self.user_data["email"])
        assert user.is_email_verified is True

    def test_email_verification_with_invalid_token(self) -> None:
        """
        Tests the email verification process with an invalid token.
        """
        # Simulate user registration
        self.client.post(self.register_url, data=self.user_data)

        # Extract the real uidb64 from the email
        email = mail.outbox[0]
        uidb64, _ = extract_uidb64_and_token_from_email(email.body)

        # Use an invalid token
        invalid_token = "invalid-token"

        # Construct the verification URL with the invalid token
        verification_url_with_invalid_token = reverse(
            "api:users:verify_email", args=[uidb64, invalid_token]
        )
        # Simulate clicking the verification link with an invalid token
        response = self.client.get(verification_url_with_invalid_token)
        assert response.status_code == 400  # or the appropriate status code for failure

        # Fetch the user and check if the email is still not verified
        user = User.objects.get(email=self.user_data["email"])
        assert user.is_email_verified is False


@pytest.mark.django_db
class TestEmailVerificationEndpoint(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        with patch("factory.django.mute_signals"):
            self.user = UserFactory.create()

    def test_user_ref_endpoint(self):
        url = reverse("api:users:my_ref_data")
        self.client.force_authenticate(self.user)
        response = self.client.get(url)

        assert response.status_code == 200
        assert response.data["referral_code"]
        assert response.data["invited_users"] == 0
