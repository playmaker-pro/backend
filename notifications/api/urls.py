"""
URL configuration for the notifications API.
"""

from django.urls import path
from rest_framework import routers

from notifications.api import views

router = routers.SimpleRouter(trailing_slash=False)


urlpatterns = [
    path(
        "",
        views.NotificationsView.as_view({"get": "get_notifications"}),
        name="get_notifications",
    ),
    path(
        "<int:notification_id>/",
        views.NotificationsView.as_view({"post": "mark_as_read"}),
        name="mark_as_read",
    ),
]
