from django.conf import settings
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView
from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.views import get_schema_view
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.core import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

import app.urls
import clubs.urls
import fantasy.urls
import followers.urls  # @to be removed
import fqa.urls
import landingpage.urls
import marketplace.urls
import plays.urls
import products.urls
import profiles.urls
import soccerbase.urls
from api import urls as api_urls
from search import views as search_views

from .api import api_router
from .settings.auth import isStaffPermission

admin.site.site_header = "PlayMaker.pro - development"
admin.site.site_title = "PlayMaker.pro - Admin site"


swagger_urls = [
    path("api/v3/", include(api_urls, namespace="api")),
]


class CustomSchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=True):
        """
        Return a custom `Schema` instance.
        We want to change the "swagger" field to "openapi" for our Frontend.
        """
        schema = super().get_schema(request, public)
        schema.pop("swagger")
        schema["openapi"] = "3.0.0"

        return schema


schema_view = get_schema_view(
    openapi.Info(
        title="Webapp API",
        default_version="v2",
        description="Webapp api description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="biuro.playmaker.pro@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    patterns=swagger_urls,
    authentication_classes=(isStaffPermission,),
    generator_class=CustomSchemaGenerator,
)


urlpatterns = [
    path("django-admin/", admin.site.urls, name="django_admin"),
    path("app/", include(app.urls), name="app"),
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path(
        "project/",
        TemplateView.as_view(template_name="subpages/project_goals.html"),
        name="home_goals",
    ),
    path("search/", search_views.search, name="search"),
    path("tables/", include(soccerbase.urls), name="soccerbase"),
    path("rozgrywki/", include(plays.urls), name="plays"),
    path("clubs/", include(clubs.urls), name="clubs"),
    path("users/", include(profiles.urls), name="profiles"),
    path("marketplace/", include(marketplace.urls), name="marketplace"),
    path("products/", include(products.urls), name="products"),
    path("fantasy/", include(fantasy.urls), name="fantasy"),
    path("najczesciej-zadawane-pytania/", include(fqa.urls), name="faqs"),
    path("feeds/", include(followers.urls), name="feeds"),
    path("policy/", TemplateView.as_view(template_name="subpgaes/policy.html")),
    path("terms/", TemplateView.as_view(template_name="subpgaes/terms.html")),
    path("blog/", include("blog.urls", namespace="blog")),
    path("api/v2/", api_router.urls),
    path("api/v3/", include(api_urls, namespace="api")),
    path(
        "api/v3/swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("api/v3/", include(api_urls, namespace="api")),
    path("resources/", include("resources.urls", namespace="resources")),
    path("select2/", include("django_select2.urls")),
    path("transfer/", include(landingpage.urls, namespace="landingpage")),
    path("", include("allauth.urls")),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
] + settings.REDIRECTS_LISTS


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

    urlpatterns += [
        path(
            "api/v3/swagger.yaml",
            schema_view.without_ui(cache_timeout=0),
            name="schema-swagger-yaml",
        ),
    ]

urlpatterns = urlpatterns + [
    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's page serving mechanism. This should be the last pattern in
    # the list:
    path("", include(wagtail_urls)),
    # Alternatively, if you want Wagtail pages to be served from a subpath
    # of your site, rather than the site root:
    #    path("pages/", include(wagtail_urls)),
]

from django.urls import path
from django.views.generic.base import TemplateView

from .sitemaps import sitemaps

urlpatterns = urlpatterns + [
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
]

urlpatterns = urlpatterns + [
    path("sitemap.xml", sitemap, sitemaps, name="django.contrib.sitemaps.views.sitemap")
]
