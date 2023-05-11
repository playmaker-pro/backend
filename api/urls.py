from django.conf.urls import include, url
from django.urls import path

from users.api_urls import urlpatterns as users_urls
from clubs.api.api_urls import urlpatterns as clubs_urls
from profiles.api_urls import urlpatterns as profiles_urls
from roles.api_urls import urlpatterns as roles_urls

from rest_framework.authtoken import views

app_name = "api"

urlpatterns = [
    url(r"^users/", include((users_urls, "users"))),
    url(r"^clubs/", include((clubs_urls, "clubs"))),
    url(r"^profiles/", include((profiles_urls, "profiles"))),
    path("api-token-auth/", views.obtain_auth_token),
    url(r"^roles/", include((roles_urls, "roles")))
]
