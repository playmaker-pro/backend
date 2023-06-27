from typing import Optional
from django.contrib.auth import get_user_model
from profiles.models import PROFILE_TYPE
from api.schemas import RegisterSchema

User = get_user_model()


class UserService:
    """User service class for handling user operations"""

    def get_user(self, user_id: int) -> Optional[User]:
        """return User or None if it doesn't exist"""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return

    def set_role(self, user: User, role: str) -> None:
        """Set role to user"""
        user.set_role(role)

    def user_has_profile(self, user: User, profile: PROFILE_TYPE) -> bool:
        """Check if given user already has profile on given type"""
        try:
            return profile.objects.get(user=user)
        except profile.DoesNotExist:
            return False

    @staticmethod
    def register(data: dict) -> User:
        """Save User instance with given data."""

        user_schema: RegisterSchema = RegisterSchema(**data)
        user: User = User(**user_schema.user_creation_data())

        user.declared_role = None
        user.state = User.STATE_NEW
        user.username = user.email
        user.set_password(user_schema.password)

        user.save()
        return user
