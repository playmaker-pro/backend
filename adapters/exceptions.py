import logging
from typing import Dict, Type
from pydantic import BaseModel

logger = logging.getLogger("adapters")


class BaseAdapterException(Exception):
    msg = ""

    def __str__(self) -> str:
        return self.msg


class PlayerHasNoMapperException(BaseAdapterException):
    """
    Exception if player has no mapper
    """

    def __init__(self, user_id: int) -> None:
        self.msg = f"Player with user id = {user_id} has no mapper."
        logger.error(self.msg)


class WrongDataFormatException(BaseAdapterException):
    """
    Exception raised if object got incorrect data schema
    """

    def __init__(
        self, obj: object, _need: Type[BaseModel], _got: Type[BaseModel]
    ) -> None:
        self.msg = f"Wrong data format raised by {obj}, correct: {_need}, got: {_got}."
        logger.error(self.msg)


class DataShortageLogger:
    """
    Log there is not enough data to perform the action
    """

    def __init__(self, obj: object, func_name: str = "", **kwargs) -> None:
        msg = f"Method {func_name} of object {obj} has not enough data for params {kwargs} to perfom the action."
        logger.error(msg)


class PlayerMapperEntityNotFoundLogger:
    """
    Exception if player's mapper has no desired entity
    """

    def __init__(self, user_id: int, params: Dict) -> None:
        msg = f"MapperEntity for params: {params} and player with user id = {user_id} not found."
        logger.error(msg)
