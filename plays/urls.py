from django.urls import path

from . import views

app_name = "plays"

urlpatterns = [
    path("", views.PlaysListViews.as_view(), name="list"),
    path("<slug:slug>/", views.PlaysViews.as_view(), name="summary"),
    path("<slug:slug>/wyniki", views.PlaysScoresViews.as_view(), name="scores"),
    path("<slug:slug>/tabela", views.PlaysTableViews.as_view(), name="table"),
    path("<slug:slug>/spotkania", views.PlaysGamesViews.as_view(), name="next_games"),
    path(
        "<slug:slug>/playmaker", views.PlaysPlaymakerViews.as_view(), name="playmaker"
    ),
]
