from django.urls import path
from rest_framework import routers
from .apis import ProfileAPI, PlayerPositionAPI
from resources.views import WebhookPlayer

router = routers.SimpleRouter(trailing_slash=False)
router.register("", ProfileAPI, basename="profiles")

urlpatterns = [
    path(
        r"",
        ProfileAPI.as_view({"post": "create_profile", "patch": "update_profile"}),
        name="create_or_update_profile",
    ),
    path(
        r"<uuid:profile_uuid>/",
        ProfileAPI.as_view({"get": "get_profile_by_uuid"}),
        name="get_profile",
    ),
    path(r"playerupdate/", WebhookPlayer.as_view(), name="player_webhook"),
    path(
        r"player_positions/",
        PlayerPositionAPI.as_view({"get": "list_positions"}),
        name="positions_list",
    ),
]
