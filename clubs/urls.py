from django.urls import path
from . import views

app_name = "clubs"

urlpatterns = [

    path("club/<slug:slug>/", views.ClubShow.as_view(), name="show_club"),
    path("team/<slug:slug>/", views.TeamShow.as_view(), name="show_team"),
]
