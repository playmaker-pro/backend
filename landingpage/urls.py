from django.urls import path
from . import views
from .api.views import TestFormAPIView

app_name = "landingpage"

urlpatterns = [

    path("", views.LandingPage.as_view(), name="landingpage"),
    path("test-form/", TestFormAPIView.as_view(), name="landingpage"),

]
