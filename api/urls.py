from django.conf.urls import include, url

from api import views
from clubs.api.api_urls import urlpatterns as clubs_urls
from events.urls import urlpatterns as events_urls
from features.api_urls import urlpatterns as features_urls
from inquiries.api.urls import urlpatterns as inquiries_urls
from labels.api.urls import urlpatterns as labels_urls
from notifications.api.urls import urlpatterns as notifications_urls
from payments.api.urls import urlpatterns as payments_urls
from profiles.api.urls import urlpatterns as profiles_urls
from roles.api_urls import urlpatterns as roles_urls
from users.api.urls import urlpatterns as users_urls

app_name = "api"

urlpatterns = [
    url(r"^users/", include((users_urls, "users"))),
    url(r"^clubs/", include((clubs_urls, "clubs"))),
    url(r"^profiles/", include((profiles_urls, "profiles"))),
    url(r"^roles/", include((roles_urls, "roles"))),
    url(r"^features/", include((features_urls, "features"))),
    url(r"^events/", include((events_urls, "events"))),
    url(r"^inquiries/", include((inquiries_urls, "inquiries"))),
    url(r"^notifications/", include((notifications_urls, "notifications"))),
    url(r"^labels/", include((labels_urls, "labels"))),
    url(r"^payments/", include((payments_urls, "payments"))),
    url(
        r"^countries/",
        views.LocaleDataView.as_view({"get": "list_countries"}),
        name="countries_list",
    ),
    url(
        r"^cities/",
        views.LocaleDataView.as_view({"get": "list_cities"}),
        name="cities_list",
    ),
    url(
        r"^preference-choices/",
        views.PreferenceChoicesView.as_view({"get": "list_preference_choices"}),
        name="preference_choices_list",
    ),
    url(
        r"^languages/",
        views.LocaleDataView.as_view({"get": "list_languages"}),
        name="languages_list",
    ),
    url(
        r"^my-city/",
        views.LocaleDataView.as_view({"get": "get_my_city"}),
        name="get_my_city",
    ),
]
