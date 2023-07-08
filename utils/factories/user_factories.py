import factory
from django.contrib.auth import get_user_model
from django.db.models import signals

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("email",)

    email = factory.Faker("email")
    username = factory.Faker("user_name")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")

    @classmethod
    @factory.django.mute_signals(signals.post_save)
    def create(cls, *args, **kwargs) -> User:
        """Override create() method to hash user password"""
        instance: User = super().create(*args, **kwargs)
        instance.set_password(kwargs.get("password", "test"))
        instance.save()
        return instance

    @classmethod
    def create_batch_force_order(cls, _count: int):
        for i in range(_count):
            cls.create(id=i + 1)
