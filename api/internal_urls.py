"""
Internal API URLs - Secured endpoints for internal services
"""
from django.conf.urls import include, url
from mapper.api.urls import urlpatterns as mapper_urls

app_name = "internal"

urlpatterns = [
    # Mapper internal endpoints
    url(r"^mapper/", include((mapper_urls, "mapper"))),
]