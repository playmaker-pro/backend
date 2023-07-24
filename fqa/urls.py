from django.urls import path
from . import views

# from . import api


app_name = "fqa"


urlpatterns = [
    path("", views.FaqView.as_view(), name="faqs"),
]
