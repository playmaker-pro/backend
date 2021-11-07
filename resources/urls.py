from .views import WebhookPlayer
from django.urls import path
from rest_framework.authtoken import views


app_name = "resources"


urlpatterns = [
    path("playerupdate", WebhookPlayer.as_view(), name="player_webhook"),
    path('api-token-auth/', views.obtain_auth_token)
]
