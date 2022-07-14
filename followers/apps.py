from django.apps import AppConfig


class FollowersConfig(AppConfig):
    name = "followers"

    def ready(self):
        from . import verbs  # noqa
