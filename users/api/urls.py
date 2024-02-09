from django.urls import path
from rest_framework import routers
from rest_framework_simplejwt.views import TokenBlacklistView

from users.api import views

router = routers.SimpleRouter(trailing_slash=False)


router.register("", views.UsersAPI, basename="users")


urlpatterns = [
    path(
        "register/",
        views.UserRegisterEndpointView.as_view({"post": "register"}),
        name="api-register",
    ),
    path("login/", views.LoginView.as_view(), name="api-login"),
    # Logout is basically a blacklist of the token, because JWT is stateless.
    # Token will expire after given (in settings) time.
    # It means that token will be valid for API calls for that time.
    path("logout/", TokenBlacklistView.as_view(), name="api-logout"),
    path(
        "refresh-token/", views.RefreshTokenCustom.as_view(), name="api-token-refresh"
    ),
    path(
        "feature-sets/",
        views.UsersAPI.as_view({"get": "feature_sets"}),
        name="feature-sets",
    ),
    path(
        "feature-elements/",
        views.UsersAPI.as_view({"get": "feature_elements"}),
        name="feature-elements",
    ),
    path(
        "google-oauth2/",
        views.UsersAPI.as_view({"post": "google_auth"}),
        name="google-oauth2",
    ),
    path(
        "facebook-oauth2/",
        views.UsersAPI.as_view({"post": "facebook_auth"}),
        name="facebook-auth",
    ),
    path(
        "email-verification/",
        views.EmailAvailability.as_view({"post": "verify_email"}),
        name="email-verification",
    ),
    path(
        "password/reset/",
        views.PasswordManagementAPIView.as_view({"post": "reset_password"}),
        name="api-password-reset",
    ),
    path(
        "password/reset/new-password/<uidb64>/<token>/",
        views.PasswordManagementAPIView.as_view({"post": "create_new_password"}),
        name="api-password-reset-confirm",
    ),
    path(
        "picture/",
        views.UserManagementAPI.as_view({"post": "update_profile_picture"}),
        name="update_profile_picture",
    ),
    path(
        "me/",
        views.UsersAPI.as_view({"get": "my_main_profile"}),
        name="my_main_profile",
    ),
    path(
        "verify-email/<str:uidb64>/<str:token>/",
        views.UserRegisterEndpointView.as_view({"get": "verify_email"}),
        name="verify_email",
    ),
]
