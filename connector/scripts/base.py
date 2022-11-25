from connector.service import HttpService


class BaseCommand:

    def __init__(self, http: HttpService = None, *args, **kwargs):
        self.http: HttpService = http
        self.handle()

    def handle(self): ...
