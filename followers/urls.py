from django.urls import include, path
from django.contrib import admin
from django.conf import settings
import django.contrib.auth

from . import views

urlpatterns = [
    path(r"", views.trending, name="trending"),
    # the three feed pages
    path(r"feed/", views.feed, name="feed"),
    path(r"aggregated_feed/", views.aggregated_feed, name="aggregated_feed"),
    # a page showing the users profile
    path(r"profile/<str:id>/", views.profile, name="profile"),
    # backends for follow and pin
    path(r"pin/", views.pin, name="pin"),
    path(r"follow/", views.follow, name="follow"),
]

# make sure we register verbs when django starts
from . import verbs
