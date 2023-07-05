from django.conf.urls import include, url
from api.views import CitiesView
from api.views import CountriesView
from users.api_urls import urlpatterns as users_urls
from clubs.api.api_urls import urlpatterns as clubs_urls
from roles.api_urls import urlpatterns as roles_urls
from profiles.api_urls import urlpatterns as profiles_urls

app_name = "api"

urlpatterns = [
    url(r"^users/", include((users_urls, "users"))),
    url(r"^clubs/", include((clubs_urls, "clubs"))),
    url(r"^profiles/", include((profiles_urls, "profiles"))),
    url(r"^roles/", include((roles_urls, "roles"))),
    url(
        r"^countries/",
        CountriesView.as_view({"get": "list_countries"}),
        name="countries_list",
    ),
    url(
        r"^cities/",
        CitiesView.as_view({"get": "list_cities"}),
        name="cities_list",
    ),
]
