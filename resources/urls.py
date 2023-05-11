from django.urls import include, path
from rest_framework import routers

from clubs.api.views import (
    TeamViewSet,
)


app_name = "resources"

api_router = routers.DefaultRouter()
api_router.register(r"teams", TeamViewSet)


urlpatterns = [
    path("", include(api_router.urls)),
    # path("api-auth/", include("rest_framework.urls")),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]
