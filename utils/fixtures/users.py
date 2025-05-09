import pytest
from django.contrib.auth import get_user_model

from .utils import fake

User = get_user_model()


@pytest.fixture
def user():
    """Create a user instance."""
    return User.objects.create(
        username=fake.user_name(),
        email=fake.email(),
        password=fake.password(),
        first_name=fake.first_name(),
        last_name=fake.last_name(),
    )
