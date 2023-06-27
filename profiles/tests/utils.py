from profiles.models import PROFILE_TYPE, MODEL_MAP
from django.contrib.auth import get_user_model

User = get_user_model()


def get_profile_by_role(role: str) -> PROFILE_TYPE:
    """get profile type (class) for given role"""
    return MODEL_MAP[role]


def get_user(user_id: int) -> User:
    """get user with given id"""
    return User.objects.get(id=user_id)


def get_random_user() -> User:
    """get random object of given model"""
    return User.objects.order_by("?")[0]
