from django.urls import path
from rest_framework import routers

from mailing.api import views

router = routers.SimpleRouter(trailing_slash=False)

urlpatterns = [
    path(
        "preferences/",
        views.MailingAPIEndpoint.as_view({
            "get": "get_my_preferences",
            "patch": "update_my_preferences",
        }),
        name="get_user_preferences",
    ),
    path(
        "<uuid:preferences_uuid>/<str:mailing_type>/unsubscribe/",
        views.update_preferences_directly,
        name="update_preferences_directly",
    ),
]
