from django.urls import path
from rest_framework import routers

from clubs.api import views

router = routers.SimpleRouter(trailing_slash=False)


urlpatterns = [
    path(
        "team-histories/search/",
        views.TeamHistorySearchApi.as_view(),
        name="team_histories_search",
    ),
    path("clubs/search/", views.ClubSearchApi.as_view(), name="clubs_search"),
    path(
        "clubs/",
        views.ClubsAPI.as_view({"get": "get_all"}),
        name="get_all_clubs",
    ),
    path(
        "club-teams/",
        views.ClubsAPI.as_view({"get": "get_all"}),
        name="get_all_clubs_teams",
    ),
    path(
        "club-teams/search/",
        views.ClubTeamsSearchApi.as_view(),
        name="club_teams_search",
    ),
    path(
        "teams/<int:team_id>",
        views.TeamsAPI.as_view({"get": "get_team"}),
        name="get_team",
    ),
    path(
        "teams/<int:team_id>/labels",
        views.TeamsAPI.as_view({"get": "get_team_labels"}),
        name="get_team_labels",
    ),
    # TODO(rkesik): that is to do
    # path(
    #     "<int:club_id>/labels",
    #     views.TeamsAPI.as_view({"get": "get_club_labels"}),
    #     name="get_club_labels",
    # ),
    path("teams/search/", views.TeamSearchApi.as_view(), name="teams_search"),
    path(
        "leagues/highest-parents/",
        views.LeagueAPI.as_view({"get": "get_highest_parents"}),
        name="highest_parent_leagues",
    ),
    # TODO: Move this to a separate 'seasons' app. Ticket: PM20-328
    path(
        "seasons/", views.SeasonAPI.as_view({"get": "list_seasons"}), name="season-list"
    ),
]
