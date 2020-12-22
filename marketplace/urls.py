from django.urls import path
from . import views

app_name = "marketplace"

urlpatterns = [

    path("/", views.AnnouncementsView.as_view(), name="announcements"),
    path("add/", views.AddAnnouncementView.as_view(), name="add_announcement"),

]
