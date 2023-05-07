from unittest import TestCase

import pytest
from django.contrib.auth import get_user_model

from users.services import UserService

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
            "last_name": "last_name"
        }
        user: User = self.user_service.register(data)

        assert isinstance(user, User)
        assert user.email == data["email"]
        assert user.first_name == data["first_name"]
