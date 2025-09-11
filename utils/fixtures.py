import pytest
from faker import Faker

from users.models import User

fake = Faker()


@pytest.fixture
def user():
    return User.objects.create_user(
        email=fake.email(),
        password=fake.password(),
        first_name=fake.first_name(),
        last_name=fake.last_name(),
    )
