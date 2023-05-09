from django.urls import path
from rest_framework import routers

from resources.views import WebhookPlayer

router = routers.SimpleRouter(trailing_slash=False)


urlpatterns = [
    path("playerupdate", WebhookPlayer.as_view(), name="player_webhook"),
]
