from django.urls import path
from rest_framework import routers
from . import apis as views

# from resources.views import WebhookPlayer

router = routers.SimpleRouter(trailing_slash=False)
router.register("", views.ProfileAPI, basename="profiles")

urlpatterns = [
    path(
        r"",
        views.ProfileAPI.as_view({"post": "create_profile", "patch": "update_profile"}),
        name="create_or_update_profile",
    ),
    path(
        r"<uuid:profile_uuid>/",
        views.ProfileAPI.as_view({"get": "get_profile_by_uuid"}),
        name="get_profile",
    ),
    # path(r"playerupdate/", WebhookPlayer.as_view(), name="player_webhook"), DEPRECATED: PM20-245
    path(
        r"formations/",
        views.FormationChoicesView.as_view({"get": "list_formations"}),
        name="formations_list",
    ),
]
