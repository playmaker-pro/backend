import logging
from typing import Dict, Type
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PlayerHasNoMapperException(Exception):
    """
    Exception if player has no mapper
    """

    def __init__(self, user_id: int) -> None:
        self.msg = f"Player with user id = {user_id} has no mapper."
        logger.error(self.msg)

    def __str__(self) -> str:
        return self.msg


class PlayerMapperEntityNotFoundException(Exception):
    """
    Exception if player's mapper has no desired entity
    """

    def __init__(self, user_id: int, params: Dict) -> None:
        self.msg = f"MapperEntity for params: {params} and player with user id = {user_id} not found."
        logger.error(self.msg)

    def __str__(self) -> str:
        return self.msg


class ObjectNotFoundException(Exception):
    """
    Exception if object was not found
    """

    def __init__(self, _id: str, _type: Type[BaseModel]) -> None:
        self.msg = f"{_type} with id = {_id} not found in database."
        logger.error(self.msg)

    def __str__(self) -> str:
        return self.msg


class WrongDataFormatException(Exception):
    """
    Exception raised if object got incorrect data schema
    """

    def __init__(
        self, obj: object, _need: Type[BaseModel], _got: Type[BaseModel]
    ) -> None:
        self.msg = f"Wrong data format raised by {obj}, correct: {_need}, got: {_got}."
        logger.error(self.msg)

    def __str__(self) -> str:
        return self.msg
