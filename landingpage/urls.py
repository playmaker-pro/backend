from django.urls import path
from . import views
from .api.views import TestFormAPIView

app_name = "landingpage"

urlpatterns = [

    path("", views.LandingPage.as_view(), name="landingpage"),
    path("test-form/<int:pk>/", TestFormAPIView.as_view(), name="landingpage"),
    path("we-got-it/<int:pk>/", views.WeGotIt.as_view(), name="wegotit"),
    path("we-got-it-success/", views.WeGotItSuccess.as_view(), name="wegotit-success"),
]
