import typing
from abc import ABC


class Strategy(ABC):
    UPDATE_AFTER: typing.Union[int, None] = None  # days count


class AlwaysUpdate(Strategy):
    UPDATE_AFTER = 0


class JustGet(Strategy):
    ...


class GetOrUpdate(Strategy):
    UPDATE_AFTER = 3
