from django.urls import path
from . import views
from . import api


app_name = "marketplace"

urlpatterns = [
    path("", views.AnnouncementsView.as_view(), name="announcements"),
    path("my/", views.MyAnnouncementsView.as_view(), name="my_announcements"),
    path(
        "club_for_player/",
        views.ClubForPlayerAnnouncementsView.as_view(),
        name="club_for_player_announcements",
    ),
    path(
        "coach_for_club/",
        views.CoachForClubAnnouncementsView.as_view(),
        name="coach_for_club_announcements",
    ),
    path(
        "club_for_coach/",
        views.ClubForCoachAnnouncementsView.as_view(),
        name="club_for_coach_announcements",
    ),
    path(
        "player_for_club/",
        views.PlayerForClubAnnouncementsView.as_view(),
        name="player_for_club_announcements",
    ),
    path("my/", views.MyAnnouncementsView.as_view(), name="my_announcements"),
    path("add/", views.AddAnnouncementView.as_view(), name="add_announcement"),
    path("approve/", api.approve_announcement, name="approve_announcement"),
]
