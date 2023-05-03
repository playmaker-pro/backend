from django.urls import include, path
from rest_framework import routers
from rest_framework.authtoken import views

from clubs.api.views import (
    ClubSearchApi,
    TeamHistorySearchApi,
    TeamSearchApi,
    TeamViewSet,
)

from .views import WebhookPlayer

app_name = "resources"

api_router = routers.DefaultRouter()
api_router.register(r"teams", TeamViewSet)


urlpatterns = [
    path("", include(api_router.urls)),
    path("teams_search", TeamSearchApi.as_view(), name="teams_search"),
    path("teams_history_search", TeamHistorySearchApi.as_view()),
    path("clubs_search", ClubSearchApi.as_view(), name="clubs_search"),
    path("playerupdate", WebhookPlayer.as_view(), name="player_webhook"),
    path("api-token-auth/", views.obtain_auth_token),
    # path("api-auth/", include("rest_framework.urls")),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]
