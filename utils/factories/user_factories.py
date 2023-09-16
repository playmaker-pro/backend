import factory
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db.models import signals
from factory import fuzzy

from users.models import UserPreferences

from .base import CustomObjectFactory

User = get_user_model()


@factory.django.mute_signals(signals.post_save)
class UserFactory(CustomObjectFactory):
    class Meta:
        model = User
        django_get_or_create = ("email",)

    email = factory.Faker("email")
    username = factory.Faker("user_name")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    password = make_password("test")
    state = User.STATE_ACCOUNT_VERIFIED

    @classmethod
    def create_admin_user(
        cls, email: str = "admin@playmaker.pro", password: str = "admin", **kwargs
    ):
        super().create(
            email=email,
            is_superuser=True,
            is_staff=True,
            password=make_password(password),
            **kwargs
        )

    @classmethod
    @factory.django.mute_signals(signals.post_save)
    def create(cls, *args, **kwargs) -> User:
        """Override create() method to hash user password"""
        kwargs["password"] = make_password(kwargs.get("password", "test"))
        instance: User = super().create(*args, **kwargs)
        return instance

    @classmethod
    def create_batch_force_order(cls, _count: int):
        for i in range(_count):
            cls.create(id=i + 1)


class UserPreferencesFactory(CustomObjectFactory):
    user = factory.SubFactory(UserFactory)
    gender = fuzzy.FuzzyChoice(["M", "K"])

    class Meta:
        model = UserPreferences
        django_get_or_create = ("user",)
