from django.urls import path
from rest_framework import routers


from roles import apis

router = routers.SimpleRouter(trailing_slash=False)

router.register("", apis.RolesAPI, basename="roles")


urlpatterns = [
    path("get-roles/", apis.RolesAPI.as_view({"get": "list"}), name="get_roles"),
]
