from api.schemas import RegisterSchema

from profiles.models import User


class UserService:
    """User service class for handling user operations"""

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
