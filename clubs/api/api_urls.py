from django.urls import path
from rest_framework import routers

from clubs.api.views import TeamSearchApi, TeamHistorySearchApi, ClubSearchApi

router = routers.SimpleRouter(trailing_slash=False)


urlpatterns = [
    path("teams_search", TeamSearchApi.as_view(), name="teams_search"),
    path("teams_history_search", TeamHistorySearchApi.as_view()),
    path("clubs_search", ClubSearchApi.as_view(), name="clubs_search"),
]