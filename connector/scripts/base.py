from typing import Union

from connector.service import HttpService, JsonService


class BaseCommand:
    def __init__(
        self, service: Union[HttpService, JsonService] = None, *args, **kwargs
    ):
        self.service: Union[HttpService, JsonService] = service
        self.handle()

    def handle(self):
        ...
