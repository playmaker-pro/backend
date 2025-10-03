import string
from unittest.mock import patch

import factory
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db.models import signals
from factory import fuzzy
from factory.fuzzy import FuzzyText

from users.models import Ref, UserPreferences, UserRef

from .base import CustomObjectFactory

User = get_user_model()


@factory.django.mute_signals(signals.post_save)
class UserFactory(CustomObjectFactory):
    class Meta:
        model = User
        django_get_or_create = ("email",)

    email = factory.Faker("email")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    password = make_password("test")
    state = User.STATE_ACCOUNT_VERIFIED
    userpreferences = factory.RelatedFactory(
        "utils.factories.user_factories.UserPreferencesFactory", "user"
    )
    userinquiry = factory.RelatedFactory(
        "utils.factories.inquiry_factories.UserInquiryFactory", "user"
    )
    ref = factory.RelatedFactory("utils.factories.user_factories.RefFactory", "user")
    display_status = User.DisplayStatus.VERIFIED
    mailing = factory.RelatedFactory(
        "utils.factories.mailing_factories.MailingFactory", "user"
    )
    is_email_verified = True

    @classmethod
    def create_admin_user(
        cls, email: str = "admin@playmaker.pro", password: str = "admin", **kwargs
    ):
        super().create(
            email=email,
            is_superuser=True,
            is_staff=True,
            password=make_password(password),
            **kwargs,
        )

    @classmethod
    def create(cls, **kwargs) -> User:
        """Override create() method to hash user password"""
        kwargs["password"] = make_password(kwargs.get("password", "test"))
        kwargs.setdefault("display_status", User.DisplayStatus.VERIFIED)

        with patch("users.tasks.prepare_new_user"):
            return super().create(**kwargs)

    @factory.post_generation
    def post_create(self, create, extracted, **kwargs):
        if not create:
            return

        # Create UserPreferences for the user
        UserPreferencesFactory(user=self)
        RefFactory(user=self)


class UserPreferencesFactory(CustomObjectFactory):
    user = factory.SubFactory(UserFactory)
    gender = fuzzy.FuzzyChoice(["M", "K"])
    birth_date = factory.Faker("date_of_birth")
    citizenship = factory.List(["PL"])
    dial_code = factory.Faker("pyint", min_value=0, max_value=1000)
    phone_number = FuzzyText(length=4, chars=string.digits)
    contact_email = factory.Faker("email")

    class Meta:
        model = UserPreferences
        django_get_or_create = ("user",)


class RefFactory(CustomObjectFactory):
    class Meta:
        model = Ref
        django_get_or_create = ("user",)


class UserRefFactory(CustomObjectFactory):
    class Meta:
        model = UserRef
        django_get_or_create = ("user",)

    user = factory.SubFactory(UserFactory)
    ref_by = factory.SubFactory(RefFactory)
