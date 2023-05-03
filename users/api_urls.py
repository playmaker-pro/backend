from django.urls import include, path
from rest_framework import routers

from users import apis

router = routers.SimpleRouter(trailing_slash=False)


router.register("", apis.UsersAPI, basename="users")


urlpatterns = [
    # path(
    #     r"users/",
    #     include(router.urls),
    # ),
    path(
        r"hello/",
        apis.UsersAPI.as_view({"get": "list"}),
        name="admin-view",
    ),
]
