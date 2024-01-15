from django.urls import path
from django.views.generic import TemplateView

app_name = "app"


urlpatterns = [
    path(
        "missing-permissions",
        TemplateView.as_view(template_name="platform/permission_denied.html"),
        name="permission_denied",
    ),
]
