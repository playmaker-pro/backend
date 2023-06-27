from django.urls import path
from rest_framework import routers
from .apis import ProfileAPI
from resources.views import WebhookPlayer

router = routers.SimpleRouter(trailing_slash=False)
router.register("", ProfileAPI, basename="profiles")

urlpatterns = [
    path(
        r"",
        ProfileAPI.as_view({"post": "create"}),
        name="create_profile",
    ),
    path(r"playerupdate/", WebhookPlayer.as_view(), name="player_webhook"),
]
