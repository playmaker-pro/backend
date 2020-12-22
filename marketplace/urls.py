from django.urls import path
from . import views
from . import api
app_name = "marketplace"

urlpatterns = [

    path("", views.AnnouncementsView.as_view(), name="announcements"),
    path("add/", views.AddAnnouncementView.as_view(), name="add_announcement"),
    path("approve/", api.approve_announcement, name="approve_announcement"),

]
