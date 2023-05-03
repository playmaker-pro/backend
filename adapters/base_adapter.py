import typing

from pm_core.services.scrapper_service import ScrapperAPI
from pm_core.services.stubs.base import ScrapperAPIStub

from adapters.strategy import Strategy

API_METHOD = typing.Union[ScrapperAPI, ScrapperAPIStub]


class BaseAdapter:
    """Base adapter class"""

    def __init__(
        self,
        strategy: typing.Type[Strategy],
        api_method: typing.Type[API_METHOD] = ScrapperAPI,
        meta: typing.Dict = None,
    ) -> None:
        self.strategy: Strategy = strategy()
        self.meta: typing.Dict = meta
        self.api: API_METHOD = api_method()

    def resolve_strategy(self) -> typing.Dict:
        """
        Configure params to fetch data based on defined strategy
        """
        return {
            attr.lower(): getattr(self.strategy, attr)
            for attr in dir(self.strategy)
            if not callable(getattr(self.strategy, attr)) and not attr.startswith("_")
        }
