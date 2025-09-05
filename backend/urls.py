from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from api import urls as api_urls

admin.site.site_header = "PlayMaker.pro - development"
admin.site.site_title = "PlayMaker.pro - Admin site"


urlpatterns = [
    path("django-admin/", admin.site.urls, name="django_admin"),
    path("api/v3/", include(api_urls, namespace="api")),
    path("select2/", include("django_select2.urls")),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("users/", include("users.urls", namespace="users")),
]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
