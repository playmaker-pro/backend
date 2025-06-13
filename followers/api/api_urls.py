from django.urls import path
from rest_framework import routers

from followers.api import views

router = routers.SimpleRouter(trailing_slash=False)

urlpatterns = [
    path(
        "my-follows/",
        views.FollowAPIView.as_view({"get": "list_followed_objects"}),
        name="get_user_follows",
    ),
    path(
        "",
        views.FollowAPIView.as_view({"get": "list_my_followers"}),
        name="get_followers",
    ),
    path(
        "my-follows/",
        views.FollowAPIView.as_view({"get": "list_followed_objects"}),
        name="get_user_follows",
    ),
    path(
        "profile/<uuid:profile_uuid>/follow/",
        views.FollowAPIView.as_view({"post": "follow_profile"}),
        name="follow_profile",
    ),
    path(
        "profile/<uuid:profile_uuid>/unfollow/",
        views.FollowAPIView.as_view({"delete": "unfollow_profile"}),
        name="unfollow_profile",
    ),
    path(
        "team/<int:team_id>/follow/",
        views.FollowAPIView.as_view({"post": "follow_team"}),
        name="follow_team",
    ),
    path(
        "team/<int:team_id>/unfollow/",
        views.FollowAPIView.as_view({"delete": "unfollow_team"}),
        name="unfollow_team",
    ),
    path(
        "club/<int:club_id>/follow/",
        views.FollowAPIView.as_view({"post": "follow_club"}),
        name="follow_club",
    ),
    path(
        "club/<int:club_id>/unfollow/",
        views.FollowAPIView.as_view({"delete": "unfollow_club"}),
        name="unfollow_club",
    ),
    path(
        "catalog/<str:catalog_slug>/follow/",
        views.FollowAPIView.as_view({"post": "follow_catalog"}),
        name="follow_catalog",
    ),
    path(
        "catalog/<str:catalog_slug>/unfollow/",
        views.FollowAPIView.as_view({"delete": "unfollow_catalog"}),
        name="unfollow_catalog",
    ),
]
