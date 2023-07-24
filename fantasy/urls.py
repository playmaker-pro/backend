from django.urls import path
from . import views

# from . import api


app_name = "fantasy"


urlpatterns = [
    path("", views.FantasyView.as_view(), name="fantasy"),
]
