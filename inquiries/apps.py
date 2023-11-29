from django.apps import AppConfig


class InquiriesConfig(AppConfig):
    name = "inquiries"

    def ready(self):
        import inquiries.signals.handlers  # noqa

