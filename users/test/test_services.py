from datetime import timedelta
from typing import List, Optional, Set
from unittest import TestCase
from unittest.mock import patch

import pytest
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone
from django.template.loader import render_to_string

from features.models import AccessPermission, Feature, FeatureElement
from roles.definitions import PLAYER_SHORT
from users.models import Ref
from users.schemas import UserGoogleDetailPydantic
from users.services import UserService
from utils.factories.feature_sets_factories import (
    AccessPermissionFactory,
    FeatureFactory,
)
from utils.factories.profiles_factories import PlayerProfileFactory
from utils.factories.social_factories import SocialAccountFactory
from utils.factories.user_factories import UserFactory, UserRefFactory
from utils.test.test_utils import TEST_EMAIL

User = get_user_model()

pytestmark = pytest.mark.django_db


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

    def test_user_creation_with_no_lastname(self) -> None:
        """Test if user is created correctly using register method"""
        data: dict = {
            "email": "test_email@test.com",
            "password": "super secret password",
            "first_name": "first_name",
        }
        user: User = self.user_service.register(data)

        assert isinstance(user, User)
        assert user.email == data["email"]
        assert user.first_name == data["first_name"]
        assert not user.last_name

    def test_user_creation_with_no_firstname(self) -> None:
        """Test if user is created correctly using register method"""
        data: dict = {
            "email": "test_email@test.com",
            "password": "super secret password",
            "last_name": "last_name",
        }
        user: User = self.user_service.register(data)

        assert isinstance(user, User)
        assert user.email == data["email"]
        assert user.last_name == data["last_name"]
        assert not user.first_name

    def test_user_creation_without_firstname_and_lastname(self) -> None:
        """Test if user is created correctly using register method"""
        data: dict = {
            "email": "test_email@test.com",
            "password": "super secret password",
        }
        user: User = self.user_service.register(data)

        assert isinstance(user, User)
        assert user.email == data["email"]
        assert not user.last_name
        assert not user.first_name

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
        user: User = self.user_service.register_from_social(
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
        user: User = self.user_service.register_from_social(
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
        user: User = self.user_service.register_from_social(
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
        provider: str = "google"
        account: Optional[SocialAccount]
        created: bool

        data = {
            "sub": "123",
            "email": TEST_EMAIL,
            "given_name": "first_name",
            "family_name": "last_name",
        }

        account, created = self.user_service.create_social_account(
            user, UserGoogleDetailPydantic(**data), provider
        )

        assert isinstance(account, SocialAccount)
        assert created

    def test_create_social_account_no_data(self) -> None:
        """Test if create_social_account method returns None if no data passed"""
        user: User = UserFactory.create()
        provider: str = "google"
        account: Optional[SocialAccount]
        created: bool

        account, created = self.user_service.create_social_account(user, {}, provider)  # type: ignore

        assert not account
        assert not created

    def test_create_social_account_exists(self) -> None:
        """
        Test if create_social_account method returns existing instance
        if account already exists
        """
        user: User = UserFactory.create()
        provider: str = "google"
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
            user, UserGoogleDetailPydantic(**data), provider
        )

        assert social_acc == account
        assert not created

    def test_email_available_method_with_false_response(self):
        """Test if email_available method returns False"""
        email: str = "some_email_address"
        res: bool = self.user_service.email_available(email)
        assert res is True

    def test_email_available_method_with_true_response(self):
        """Test if email_available method returns True"""
        email: str = "some_email_address"
        UserFactory.create(email=email)
        res: bool = self.user_service.email_available(email)
        assert res is False


class TestRefferalSystem:
    def test_create_ref_without_user(self):
        """Test if Ref can be created without user"""
        ref = Ref.objects.create(title="test-title", description="test-description")

        assert not ref.user
        assert ref.uuid
        assert ref.title == "test-title"
        assert ref.description == "test-description"

    def test_user_always_have_referral(self):
        """Test if user always have referral"""
        user = UserFactory()

        assert user.ref
        assert user.ref.referrals.count() == 0

    def test_reward_user_notify_admins(self):
        profile = PlayerProfileFactory.create()
        ref = profile.user.ref

        assert ref.registered_users.count() == 0
        assert not profile.is_premium

        for _ in range(10):
            UserRefFactory(ref_by=ref)

        last_mail = mail.outbox[-1]

        assert ref.registered_users.count() == 10
        assert (
            last_mail.subject
            == f"[Django] Osiągnięto 10 poleconych użytkowników przez {str(ref)}."
        )
        assert last_mail.body == f"Link afiliacyjny {str(ref)} osiągnął 10 poleconych."

        for _ in range(10):
            UserRefFactory(ref_by=ref)

        last_mail = mail.outbox[-1]

        assert (
            last_mail.subject
            == f"[Django] Osiągnięto 20 poleconych użytkowników przez {str(ref)}."
        )

        for _ in range(10):
            UserRefFactory(ref_by=ref)

        last_mail = mail.outbox[-1]

        assert (
            last_mail.subject
            == f"[Django] Osiągnięto 30 poleconych użytkowników przez {str(ref)}."
        )

    def test_reward_non_user_referral_after_10_invites(self):
        ref = Ref.objects.create(title="test-title", description="test-description")

        assert ref.registered_users.count() == 0

        for _ in range(10):
            UserRefFactory(ref_by=ref)

        last_mail = mail.outbox[-1]

        assert ref.registered_users.count() == 10
        assert (
            last_mail.subject
            == f"[Django] Osiągnięto 10 poleconych użytkowników przez {str(ref)}."
        )
        assert last_mail.body == f"Link afiliacyjny {str(ref)} osiągnął 10 poleconych."

    def test_failed_to_reward_user_after_10_invites(self):
        user = PlayerProfileFactory.create().user
        ref = user.ref

        assert ref.registered_users.count() == 0

        for _ in range(10):
            UserRefFactory(ref_by=ref)

        last_mail = mail.outbox[-1]

        assert ref.registered_users.count() == 10
        assert (
            last_mail.subject
            == f"[Django] Osiągnięto 10 poleconych użytkowników przez {str(ref)}."
        )
        assert last_mail.body == f"Link afiliacyjny {str(ref)} osiągnął 10 poleconych."

    def test_reward_1_referral(self):
        user = PlayerProfileFactory.create().user
        ref = user.ref

        assert ref.registered_users.count() == 0
        assert not user.profile.is_premium

        user_ref = UserRefFactory(ref_by=ref).user
        last_mails = {m.to[0]: m for m in mail.outbox[-2:]}

        assert ref.registered_users.count() == 1
        expected_subject_referrer = render_to_string(
            "mailing/mails/1_referral_reward_referrer_subject.txt",
        ).strip()
        assert last_mails[user.email].subject == expected_subject_referrer
        expected_subject_referred = render_to_string(
            "mailing/mails/referral_reward_referred_subject.txt",
        ).strip()
        assert (
            last_mails[user_ref.email].subject == expected_subject_referred
        )


    def test_reward_3_referrals(self):
        user = PlayerProfileFactory.create().user
        ref = user.ref

        assert ref.registered_users.count() == 0
        assert not user.profile.is_premium

        for _ in range(3):
            UserRefFactory(ref_by=ref)

        last_mails = {m.to[0]: m for m in mail.outbox[-1:]}

        assert ref.registered_users.count() == 3
        expected_subject = render_to_string(
            "mailing/mails/3_referral_reward_referrer_subject.txt",
        ).strip()
        assert last_mails[user.email].subject == expected_subject
        assert user.profile.is_premium
        assert (
            user.profile.premium.valid_until.date()
            == timezone.now().date() + timedelta(days=14)
        )

    def test_reward_5_referrals(self):
        user = PlayerProfileFactory.create().user
        ref = user.ref

        assert ref.registered_users.count() == 0
        assert not user.profile.is_premium

        for _ in range(5):
            UserRefFactory(ref_by=ref)

        last_mails = {m.to[0]: m for m in mail.outbox[-1:]}

        assert ref.registered_users.count() == 5
        expected_subject = render_to_string(
            "mailing/mails/5_referral_reward_referrer_subject.txt",
        ).strip()
        assert last_mails[user.email].subject == expected_subject
        assert user.profile.is_premium
        assert (
            user.profile.premium.valid_until.date()
            == timezone.now().date() + timedelta(days=30) + timedelta(days=14)
        )

    def test_reward_15_referrals(self):
        user = PlayerProfileFactory.create().user
        ref = user.ref

        assert ref.registered_users.count() == 0
        assert not user.profile.is_premium

        for _ in range(15):
            UserRefFactory(ref_by=ref)

        last_mails = {m.to[0]: m for m in mail.outbox[-1:]}

        assert ref.registered_users.count() == 15
        assert (
            last_mails[user.email].subject
            == "Gratulacje! 6 miesięcy Premium za 15 poleceń PlayMaker.pro"
        )
        assert user.profile.is_premium
        expected_subject = render_to_string(
            "mailing/mails/15_referral_reward_referrer_subject.txt",
        ).strip()
        assert last_mails[user.email].subject == expected_subject
        assert (
            user.profile.premium.valid_until.date()
            == timezone.now().date()
            + timedelta(days=180)
            + timedelta(days=30)
            + timedelta(days=14)
        )
