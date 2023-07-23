from django.urls import path
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)

from users import apis

router = routers.SimpleRouter(trailing_slash=False)


router.register("", apis.UsersAPI, basename="users")


urlpatterns = [
    path(
        r"hello/",
        apis.UsersAPI.as_view({"get": "list"}),
        name="admin-view",
    ),
    path("register/", apis.UsersAPI.as_view({"post": "register"}), name="api-register"),
    path("login/", TokenObtainPairView.as_view(), name="api-login"),
    # Logout is basically a blacklist of the token, because JWT is stateless.
    # Token will expire after given (in settings) time.
    # It means that token will be valid for API calls for that time.
    path("logout/", TokenBlacklistView.as_view(), name="api-logout"),
    path("refresh-token/", TokenRefreshView.as_view(), name="api-token-refresh"),
    path(
        "feature-sets/",
        apis.UsersAPI.as_view({"get": "feature_sets"}),
        name="feature-sets",
    ),
    path(
        "feature-elements/",
        apis.UsersAPI.as_view({"get": "feature_elements"}),
        name="feature-elements",
    ),
    path(
        "google-oauth2/",
        apis.UsersAPI.as_view({"post": "google_auth"}),
        name="google-oauth2",
    ),
]
