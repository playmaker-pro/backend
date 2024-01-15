from django.urls import re_path
from django.views.generic import RedirectView

REDIRECT_TO = "https://premiera.playmaker.pro"

urlpatterns = [
    re_path(r"^(.*)$", RedirectView.as_view(url=REDIRECT_TO), name="redirect")
]
