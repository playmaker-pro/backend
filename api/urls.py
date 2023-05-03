from django.conf.urls import include, url

from users.api_urls import urlpatterns as users_urls

urlpatterns = [
    url(r"^users/", include((users_urls, "users"))),
]
