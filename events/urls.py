from django.urls import path
from rest_framework import routers

from events import views


router = routers.SimpleRouter(trailing_slash=False)


urlpatterns = [
    path(
        "<int:event_id>/read",
        views.EventsAPI.as_view({"post": "read_event"}),
        name="read_event",
    ),
    path(
        "users/<int:user_id>/",
        views.EventsAPI.as_view({"get": "get_user_events"}),
        name="get_user_events",
    ),
]
