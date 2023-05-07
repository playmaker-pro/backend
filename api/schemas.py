from dataclasses import dataclass, fields
from typing import Set, Dict, List, Optional


@dataclass
class BaseSchema:
    @classmethod
    def values(cls):
        return {field.name for field in fields(cls)}


@dataclass
class RegisterSchema(BaseSchema):
    """Schema represents data which have to be used by register endpoint"""
    email: str
    first_name: str
    last_name: str
    password: str
    id: Optional[int] = None
    username: Optional[str] = None

    def user_creation_data(self) -> Dict[str, str]:
        """
        Return data which have to be used to create User instance.
        Password should not be included to avoid saving plain text password
        """
        excluded_fields_for_creation: List[str] = ["password", "id", "username"]
        return {key: val for key, val in self.__dict__.items() if key not in excluded_fields_for_creation}

    def values_fields(self) -> Set[str]:
        """
        Fields which have to be returned by register endpoint.
        Password should not be returned.
        """
        return {field.name for field in fields(self) if field.name != "password"}
