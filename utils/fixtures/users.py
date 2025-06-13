import pytest
from django.contrib.auth import get_user_model
from faker import Faker

from utils.factories.user_factories import UserFactory

User = get_user_model()
fake = Faker(locale="pl_PL")


@pytest.fixture
def unique_user():
    """Create a user instance."""
    yield UserFactory.create()
