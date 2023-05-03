import datetime
import logging
from typing import Dict, Type

from django.conf import settings
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


class ScrapperIsNotRespongingLogger:
    """
    Log on each minute if there is no connection with scrapper
    Create log in prod/stg env, print out in dev env
    """

    last_log = None

    def __call__(self) -> None:
        _now = datetime.datetime.now()

        if (
            self.last_log is None
            or self.last_log + datetime.timedelta(minutes=1) < _now
        ):
            self.last_log = _now
            self.log()

    def log(self):
        msg = f"!!! Scrapper is not responding ({self.last_log}) !!!"

        if settings.CONFIGURATION == "dev":
            print(msg)
        else:
            logger.error(msg)
