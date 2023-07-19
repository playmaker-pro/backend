from profiles import models
from django.contrib.auth import get_user_model
from profiles.services import ProfileService

User = get_user_model()
profile_service = ProfileService()


def get_profile_by_role(role: str) -> models.PROFILE_TYPE:
    """get profile type (class) for given role"""
    return models.PROFILE_MODEL_MAP[role]


def get_user(user_id: int) -> User:
    """get user with given id"""
    return User.objects.get(id=user_id)


def get_random_profile() -> models.PROFILE_TYPE:
    """get random profile from db"""
    return models.PlayerProfile.objects.order_by("?").first()


def create_empty_profile(data: dict) -> models.PROFILE_TYPE:
    """
    Create new profile given data.
    data: dict must include "user_id" and "role", like:
    {"user_id": userid: int, "role": "P" | "C" | ..., ...rest}
    """
    role = data.pop("role")
    profile = profile_service.get_model_by_role(role)
    return profile_service.create_profile_with_initial_data(profile, data)
