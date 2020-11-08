from django.urls import path
from . import views

app_name = "soccerbase"

urlpatterns = [

    path("players/", views.PlayersTable.as_view(), name="players"),
    path("coaches/", views.CoachesTable.as_view(), name="coaches"),
    path("teams/", views.TeamsTable.as_view(), name="teams"),
]
