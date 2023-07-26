from typing import List, Optional, Set
from unittest import TestCase
from unittest.mock import patch

import pytest
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model

from features.models import AccessPermission, Feature, FeatureElement
from roles.definitions import PLAYER_SHORT
from users.entities import UserGoogleDetailPydantic
from users.services import UserService
from utils.factories.feature_sets_factories import (AccessPermissionFactory,
                                                    FeatureFactory)
from utils.factories.social_factories import SocialAccountFactory
from utils.factories.user_factories import UserFactory
from utils.test.test_utils import TEST_EMAIL, mute_post_save_signal

User = get_user_model()


@pytest.mark.django_db
class TestUserService(TestCase):
    def setUp(self) -> None:
        self.user_service = UserService()

    def test_user_creation(self) -> None:
        """Test if user is created correctly using register method"""
        data: dict = {
            "email": "test_email@test.com",
            "password": "super secret password",
            "first_name": "first_name",
            "last_name": "last_name",
        }
        user: User = self.user_service.register(data)

        assert isinstance(user, User)
        assert user.email == data["email"]
        assert user.first_name == data["first_name"]

    def test_access_permission_filtered_by_user_role_method(self):
        """
        Test if access_permission_filtered_by_user_role method
        returns correct data
        """
        access: AccessPermission = AccessPermissionFactory.create()
        res: Set[int] = self.user_service.access_permission_filtered_by_user_role()

        assert access.pk in [obj for obj in res]
        assert isinstance(res, set)

    def test_get_user_features_method(self):
        """Test if get_user_features method returns correct data"""
        # TODO: this test is not fully usefully, because
        #  access_permission_filtered_by_user_role method
        #  returns mocked value. We should change it after Role model will be created.
        obj: Feature = FeatureFactory.create()
        # access2: AccessPermission = AccessPermissionFactory.create(role="unknown role")
        # obj.elements.first().access_permissions.add(access2)

        patch(
            "users.services.UserService.access_permission_filtered_by_user_role",
            return_value={obj.elements.first().access_permissions.first().pk},
        )
        user: User = UserFactory.create(declared_role=PLAYER_SHORT)
        res: List[Feature] = self.user_service.get_user_features(user)

        assert isinstance(res, list)
        assert isinstance(res[0], Feature)
        assert res[0].pk == obj.pk

    def test_get_user_feature_elements(self):
        """Test if get_user_feature_elements method returns correct data"""
        # TODO: this test is not fully usefully, because
        #  access_permission_filtered_by_user_role method
        #  returns mocked value. We should change it after Role model will be created.
        obj: Feature = FeatureFactory.create()
        # access2: AccessPermission = AccessPermissionFactory.create(role="unknown role")
        # obj.elements.first().access_permissions.add(access2)

        patch(
            "users.services.UserService.access_permission_filtered_by_user_role",
            return_value={obj.elements.first().access_permissions.first().pk},
        )

        user: User = UserFactory.create(declared_role=PLAYER_SHORT)
        res: List[FeatureElement] = self.user_service.get_user_feature_elements(user)

        assert isinstance(res, list)
        assert isinstance(res[0], FeatureElement)
        assert res[0].pk == obj.elements.first().pk

    def test_register_from_google(self) -> None:
        """Test if register_from_google method returns correct data"""
        data: dict = {
            "email": TEST_EMAIL,
            "given_name": "first_name",
            "family_name": "last_name",
        }
        user: User = self.user_service.register_from_google(
            UserGoogleDetailPydantic(**data)
        )

        assert isinstance(user, User)
        assert user.email == data["email"]
        assert user.first_name == data["given_name"]

    def test_register_from_google_not_valid_data(self) -> None:
        """
        Test if register_from_google method returns None if not valid data passed
        """
        data: dict = {
            "email": 1,
            "given_name": 2,
            "family_name": 3,
        }
        user: User = self.user_service.register_from_google(
            UserGoogleDetailPydantic(**data)
        )

        assert not isinstance(user, User)
        assert user is None

    def test_register_from_google_not_valid_email(self) -> None:
        """Test if register_from_google method returns None if not valid email passed"""
        data: dict = {
            "email": "email",
            "given_name": 2,
            "family_name": 3,
        }
        user: User = self.user_service.register_from_google(
            UserGoogleDetailPydantic(**data)
        )

        assert not isinstance(user, User)
        assert user is None

    def test_create_social_account_created(self) -> None:
        """
        Test if social account is created correctly.
        User doesn't have any social accounts, so we should create new one.
        """
        user: User = UserFactory.create()
        account: Optional[SocialAccount]
        created: bool

        data = {
            "sub": "123",
            "email": TEST_EMAIL,
            "given_name": "first_name",
            "family_name": "last_name",
        }

        account, created = self.user_service.create_social_account(
            user, UserGoogleDetailPydantic(**data)
        )

        assert isinstance(account, SocialAccount)
        assert created

    def test_create_social_account_no_data(self) -> None:
        """Test if create_social_account method returns None if no data passed"""
        user: User = UserFactory.create()
        account: Optional[SocialAccount]
        created: bool

        account, created = self.user_service.create_social_account(user, {})

        assert not account
        assert not created

    def test_create_social_account_exists(self) -> None:
        """
        Test if create_social_account method returns existing instance
        if account already exists
        """
        user: User = UserFactory.create()
        social_acc: SocialAccount = SocialAccountFactory.create(user=user)
        account: Optional[SocialAccount]
        created: bool
        data = {
            "sub": "123",
            "email": TEST_EMAIL,
            "given_name": "first_name",
            "family_name": "last_name",
        }

        account, created = self.user_service.create_social_account(
            user, UserGoogleDetailPydantic(**data)
        )

        assert social_acc == account
        assert not created
