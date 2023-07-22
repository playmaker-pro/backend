from django.urls import path

from . import views

app_name = "clubs"

urlpatterns = [
    path("club/<slug:slug>/", views.ClubShow.as_view(), name="show_club"),
    path("club/edit/<slug:slug>/", views.ClubEdit.as_view(), name="edit_club"),
    path("team/<slug:slug>/", views.TeamShow.as_view(), name="show_team"),
    path("team/edit/<slug:slug>/", views.TeamEdit.as_view(), name="edit_team"),
]
