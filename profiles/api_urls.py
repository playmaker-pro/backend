from django.urls import path
from rest_framework import routers

from . import apis as views

# from resources.views import WebhookPlayer

router = routers.SimpleRouter(trailing_slash=False)
router.register("", views.ProfileAPI, basename="profiles")

urlpatterns = [
    path(
        r"",
        views.ProfileAPI.as_view(
            {
                "post": "create_profile",
                "get": "get_bulk_profiles",
            }
        ),
        name="create_or_list_profiles",
    ),
    path(
        r"owned/",
        views.ProfileAPI.as_view(
            {
                "get": "get_owned_profiles",
            }
        ),
        name="get_owned_profiles",
    ),
    path(
        r"<uuid:profile_uuid>/",
        views.ProfileAPI.as_view(
            {
                "get": "get_profile_by_uuid",
                "patch": "update_profile",
            }
        ),
        name="get_or_update_profile",
    ),
    path(
        r"<uuid:profile_uuid>/labels",
        views.ProfileAPI.as_view({"get": "get_profile_labels"}),
        name="get_profile_labels",
    ),
    # path(r"playerupdate/", WebhookPlayer.as_view(), name="player_webhook"), DEPRECATED: PM20-245
    path(
        r"formations/",
        views.FormationChoicesView.as_view({"get": "list_formations"}),
        name="formations_list",
    ),
    path(
        r"club-roles/",
        views.ProfileEnumsAPI.as_view({"get": "get_club_roles"}),
        name="club_roles",
    ),
    path(
        r"referee-roles/",
        views.ProfileEnumsAPI.as_view({"get": "get_referee_roles"}),
        name="referee_roles",
    ),
    path(
        r"coach-roles/",
        views.CoachRolesChoicesView.as_view({"get": "list_coach_roles"}),
        name="coach_roles_list",
    ),
    path(
        r"player-positions/",
        views.PlayerPositionAPI.as_view({"get": "list_positions"}),
        name="positions_list",
    ),
    path(
        r"coach-licence/",
        views.CoachLicencesAPIView.as_view(
            {
                "get": "list_coach_licences",
                "post": "add_licence_for_coach",
            }
        ),
        name="coach_licences",
    ),
    path(
        r"coach-licence/<int:licence_id>/",
        views.CoachLicencesAPIView.as_view(
            {"patch": "modify_licence_for_coach", "delete": "delete_licence_for_coach"}
        ),
        name="coach_licences_modify",
    ),
    path(
        r"players-age-range/",
        views.ProfileEnumsAPI.as_view({"get": "get_player_age_range"}),
        name="players_age_range",
    ),
    path(
        r"player-video/labels/",
        views.PlayerVideoAPI.as_view({"get": "get_labels"}),
        name="player_video_labels",
    ),
    path(
        r"player-video/",
        views.PlayerVideoAPI.as_view(
            {
                "post": "create_player_video",
                "delete": "delete_player_video",
                "patch": "update_player_video",
            }
        ),
        name="modify_player_video",
    ),
    path(
        r"player-video/<int:video_id>/",
        views.PlayerVideoAPI.as_view(
            {
                "delete": "delete_player_video",
            }
        ),
        name="delete_player_video",
    ),
    path(
        r"course/",
        views.ProfileCoursesAPI.as_view({"post": "create"}),
        name="create_course",
    ),
    path(
        r"course/<int:course_id>/",
        views.ProfileCoursesAPI.as_view({"delete": "delete", "patch": "update"}),
        name="modify_course",
    ),
    path(
        r"teams/<uuid:profile_uuid>/",
        views.ProfileTeamsApi.as_view({"get": "get_profile_team_contributor"}),
        name="profiles_teams",
    ),
    path(
        r"teams/add/",
        views.ProfileTeamsApi.as_view({"post": "add_team_contributor_to_profile"}),
        name="add_team_to_profile",
    ),
    path(
        "teams/<int:team_contributor_id>/",
        views.ProfileTeamsApi.as_view(
            {
                "patch": "update_profile_team_contributor",
                "delete": "delete_profile_team_contributor",
            }
        ),
        name="update_team_history",
    ),
]
