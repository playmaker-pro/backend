from django.conf.urls import include, url

from users.api_urls import urlpatterns as users_urls
from roles.api_urls import urlpatterns as roles_urls


urlpatterns = [
    url(r"^users/", include((users_urls, "users"))),
    url(r"^roles/", include((roles_urls, "roles")))
]
