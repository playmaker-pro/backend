from .views import WebhookPlayer
from django.urls import path, include
from rest_framework.authtoken import views
from clubs.api.views import TeamViewSet, TeamSearchApi, ClubSearchApi
from rest_framework import routers


app_name = "resources"

api_router = routers.DefaultRouter()
api_router.register(r"teams", TeamViewSet)


urlpatterns = [
    path("", include(api_router.urls)),
    path("teams_search", TeamSearchApi.as_view(), name="teams_search"),
    path("clubs_search", ClubSearchApi.as_view()),
    path("playerupdate", WebhookPlayer.as_view(), name="player_webhook"),
    path("api-token-auth/", views.obtain_auth_token),
    # path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
