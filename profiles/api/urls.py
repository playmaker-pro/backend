from django.urls import path
from rest_framework import routers

from profiles.api import views

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
        "count/",
        views.ProfileAPI.as_view(
            {
                "get": "get_filtered_profile_count",
            }
        ),
        name="filtered_profile_count",
    ),
    path(
        "search/",
        views.ProfileSearchView.as_view({"get": "search_profiles"}),
        name="profile_search",
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
        r"slug/<slug:profile_slug>/",
        views.ProfileAPI.as_view(
            {
                "get": "get_profile_by_slug",
            }
        ),
        name="get_profile_by_slug",
    ),
    path(
        r"<uuid:profile_uuid>/labels",
        views.ProfileAPI.as_view({"get": "get_profile_labels"}),
        name="get_profile_labels",
    ),
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
        r"profile-video/labels/",
        views.ProfileVideoAPI.as_view({"get": "get_labels"}),
        name="profile_video_labels",
    ),
    path(
        r"profile-video/",
        views.ProfileVideoAPI.as_view(
            {
                "post": "create_profile_video",
            }
        ),
        name="create_profile_video",
    ),
    path(
        r"profile-video/<int:video_id>/",
        views.ProfileVideoAPI.as_view(
            {
                "delete": "delete_profile_video",
                "patch": "update_profile_video",
            }
        ),
        name="modify_profile_video",
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
        r"<uuid:profile_uuid>/teams/",
        views.ProfileTeamsApi.as_view({"get": "get_profile_team_contributor"}),
        name="profiles_teams",
    ),
    path(
        r"<uuid:profile_uuid>/teams/add/",
        views.ProfileTeamsApi.as_view({"post": "add_team_contributor_to_profile"}),
        name="add_team_to_profile",
    ),
    path(
        r"<uuid:profile_uuid>/teams/<int:team_contributor_id>/",
        views.ProfileTeamsApi.as_view(
            {
                "patch": "update_profile_team_contributor",
                "delete": "delete_profile_team_contributor",
            }
        ),
        name="update_or_delete_team_contributor",
    ),
    path(
        "set-main/",
        views.ProfileAPI.as_view({"post": "set_main_profile"}),
        name="set_main_profile",
    ),
    path(
        r"<uuid:profile_uuid>/external-links/",
        views.ExternalLinksAPI.as_view(
            {
                "get": "get_profile_external_links",
                "post": "set_or_update_external_links",
                "patch": "set_or_update_external_links",
            }
        ),
        name="profile_external_links",
    ),
    path(
        r"<uuid:profile_uuid>/transfer-status/",
        views.TransferStatusAPIView.as_view(
            {
                "get": "get_profile_transfer_status",
                "patch": "update_profile_transfer_status",
                "post": "create_profile_transfer_status",
                "delete": "delete_profile_transfer_status",
            }
        ),
        name="profile_transfer_status",
    ),
    path(
        r"list-transfer-status/",
        views.TransferStatusAPIView.as_view(
            {
                "get": "list_transfer_status",
            }
        ),
        name="list_transfer_status",
    ),
    path(
        r"transfer-status/additional-info/",
        views.TransferStatusAPIView.as_view(
            {
                "get": "get_transfer_status_additional_info",
            }
        ),
        name="list_transfer_status_additional_choices",
    ),
    path(
        r"<uuid:profile_uuid>/transfer-request/",
        views.TransferRequestAPIView.as_view(
            {
                "get": "get_profile_transfer_request",
                "post": "create_transfer_request",
                "patch": "update_transfer_request",
                "delete": "delete_profile_transfer_request",
            }
        ),
        name="profile_transfer_request",
    ),
    path(
        r"transfer-request/status/",
        views.TransferRequestAPIView.as_view(
            {
                "get": "list_transfer_request_status",
            }
        ),
        name="list_transfer_request_status",
    ),
    path(
        r"transfer-request/number-of-trainings/",
        views.TransferRequestAPIView.as_view(
            {
                "get": "list_transfer_request_number_of_trainings",
            }
        ),
        name="list_transfer_request_number_of_trainings",
    ),
    path(
        r"transfer-request/benefits/",
        views.TransferRequestAPIView.as_view(
            {
                "get": "list_transfer_request_benefits",
            }
        ),
        name="list_transfer_request_benefits",
    ),
    path(
        r"transfer-request/salary/",
        views.TransferRequestAPIView.as_view(
            {
                "get": "list_transfer_request_salary",
            }
        ),
        name="list_transfer_request_salary",
    ),
    path(
        r"<uuid:profile_uuid>/transfer-request/teams/",
        views.TransferRequestAPIView.as_view(
            {
                "get": "get_profile_actual_teams",
            }
        ),
        name="list_transfer_request_actual_teams",
    ),
    #  Catalogues
    path(
        r"catalogue/transfer-request/",
        views.TransferRequestCatalogueAPIView.as_view(
            {
                "get": "list_transfer_requests",
            }
        ),
        name="list_transfer_request",
    ),
]
