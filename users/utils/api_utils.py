from rest_framework.exceptions import ValidationError

from users.errors import InvalidEmailException, UserAlreadyExists


def validate_serialized_email(error: ValidationError) -> None:
    """Validate given error and return specific Exceptions. Function used in serializers."""

    error_dict: dict = error.detail

    if "email" in error_dict:
        for element in error_dict["email"]:
            if element.code == "invalid":
                raise InvalidEmailException()
            if element.code == "unique":
                raise UserAlreadyExists()
    raise ValidationError(error_dict)
