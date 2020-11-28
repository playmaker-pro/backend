from django.conf import settings
from django.urls import include, path
from django.contrib import admin
from django.views.generic import TemplateView

from wagtail.admin import urls as wagtailadmin_urls
from wagtail.core import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

from search import views as search_views
from .api import api_router

import soccerbase.urls
import clubs.urls
import profiles.urls
import allauth.account.urls
import followers.urls  # @to be removed 
from django.views.generic import TemplateView

admin.site.site_header = 'PlayMaker.pro - development'
admin.site.site_title = 'PlayMaker.pro - Admin site'


urlpatterns = [
    path('django-admin/', admin.site.urls),

    path('admin/', include(wagtailadmin_urls)),
    path('documents/', include(wagtaildocs_urls)),
    path('project/', TemplateView.as_view(template_name='project_goals.html'), name="home_goals"),
    path('search/', search_views.search, name='search'),
    path('tables/', include(soccerbase.urls), name='soccerbase'),
    path('clubs/', include(clubs.urls), name="clubs"),
    path('users/', include(profiles.urls), name="profiles"),

    path('feeds/', include(followers.urls), name="feeds"),
    path('policy/', TemplateView.as_view(template_name='subpgaes/policy.html')),
    path('terms/', TemplateView.as_view(template_name='subpgaes/terms.html')),
    path('blog/', include('blog.urls', namespace="blog")),
    path('api/v2/', api_router.urls),
    path('', include('allauth.urls')),


]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns


urlpatterns = urlpatterns + [
    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's page serving mechanism. This should be the last pattern in
    # the list:
    path("", include(wagtail_urls)),

    # Alternatively, if you want Wagtail pages to be served from a subpath
    # of your site, rather than the site root:
    #    path("pages/", include(wagtail_urls)),
]
