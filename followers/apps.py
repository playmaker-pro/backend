from django.apps import AppConfig


class FollowersConfig(AppConfig):
    name = "followers"

    def ready(self):
        from . import signals  # noqa
        from . import verbs  # noqa
