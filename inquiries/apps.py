from django.apps import AppConfig


class InquiriesConfig(AppConfig):
    name = "inquiries"

    def ready(self):
        from inquiries import signals
