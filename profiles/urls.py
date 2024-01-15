from django.urls import path
from django.views.generic import TemplateView

from . import api, views

app_name = "profiles"


urlpatterns = [
    path(
        "me/", views.redirect_to_profile_with_full_name, name="show_self"
    ),  # views.ShowProfile.as_view(), name="show_self"),
    path("me/query/", api.inquiry, name="inquiry_me"),
    path("me/query/see/", api.inquiry_seen, name="inquiry_see"),
    path("me/query/update/", api.inquiry_update, name="inquiry_update"),
    # Deprecation(rkesik): since we are working on a new FE
    #    path("me/observe/", api.observe, name="observe_me"),
    #     path("me/observe/team/", api.observe_team, name="observe_team"),
    path(
        "me/verification/",
        views.AccountVerification.as_view(),
        name="account_verification",
    ),
    path(
        "me/updatesettings/", views.AccountSettings.as_view(), name="account_settings"
    ),
    path(
        "me/missingname/",
        views.AccountMissingFirstLastName.as_view(),
        name="account_missingname",
    ),
    path("me/edit/", views.EditProfile.as_view(), name="edit_self"),
    path(
        "me/edit/settings/", views.EditAccountSettings.as_view(), name="edit_settings"
    ),
    path("player/fantasy/", views.ProfileFantasy.as_view(), name="my_fantasy"),
    path("player/carrier/", views.ProfileCarrier.as_view(), name="my_carrier"),
    path("player/matches/", views.ProfileGames.as_view(), name="my_games"),
    path("player/videos/", views.ProfileVideoView.as_view(), name="my_videos"),
    path(
        "player/fantasy/<slug:slug>/",
        views.ProfileFantasy.as_view(),
        name="player_fantasy",
    ),
    path(
        "player/carrier/<slug:slug>/",
        views.ProfileCarrier.as_view(),
        name="player_carrier",
    ),
    path(
        "player/videos/<slug:slug>/",
        views.ProfileVideoView.as_view(),
        name="player_videos",
    ),
    path(
        "player/matches/<slug:slug>/", views.ProfileGames.as_view(), name="player_games"
    ),
    path("stats/fantasy/", views.ProfileFantasy.as_view(), name="my_stats_fantasy"),
    path("stats/carrier/", views.ProfileCarrier.as_view(), name="my_stats_carrier"),
    path("stats/matches/", views.ProfileGames.as_view(), name="my_stats_games"),
    path(
        "stats/fantasy/<slug:slug>/",
        views.ProfileFantasy.as_view(),
        name="stats_fantasy",
    ),
    path(
        "stats/carrier/<slug:slug>/",
        views.ProfileCarrier.as_view(),
        name="stats_carrier",
    ),
    path(
        "stats/matches/<slug:slug>/", views.ProfileGames.as_view(), name="stats_games"
    ),
    # Deprecation(rkesik): since we are working on a new FE
    #     path("my/observers/", views.MyObservers.as_view(), name="my_observers"),
    path("my/requests/", views.MyRequests.as_view(), name="my_requests"),
    path("me/changerole/", views.RequestRoleChange.as_view(), name="rolechange_self"),
    path("<slug:slug>/", views.ShowProfile.as_view(), name="show"),
    path(
        "howto/process/",
        TemplateView.as_view(template_name="profiles/how_to.html"),
        name="howto",
    ),
]
