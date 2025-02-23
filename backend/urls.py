from django.conf import settings
from django.contrib import admin
from django.urls import include, path

import landingpage.urls
from api import urls as api_urls

admin.site.site_header = "PlayMaker.pro - development"
admin.site.site_title = "PlayMaker.pro - Admin site"


urlpatterns = [
    path("django-admin/", admin.site.urls, name="django_admin"),
    path("api/v3/", include(api_urls, namespace="api")),
    path("transfer/", include(landingpage.urls, namespace="landingpage")),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
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
