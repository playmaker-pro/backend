from typing import Optional

from rest_framework import authentication

from profiles.models import User


class isStaffPermission(authentication.BasicAuthentication):
    """Custom authentication class to check if the user is staff."""

    def authenticate(self, request) -> Optional[User]:
        """Authenticate the user"""
        user: Optional[User, bool] = super().authenticate(request)
        if user and user[0] and user[0].is_staff:
            return user
        return None
