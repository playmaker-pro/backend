from typing import Dict

from rest_framework import status

from api.errors import CoreAPIException


class AccessForbiddenException(CoreAPIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You don't have permission to perform this operation"


class UserAlreadyExists(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "User already exists in database with that email address"
    fields = "email"


class InvalidEmailException(CoreAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid email address"
    fields = "email"
