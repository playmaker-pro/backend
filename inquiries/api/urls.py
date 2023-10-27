from django.urls import path
from rest_framework import routers

from inquiries.api import views

router = routers.SimpleRouter(trailing_slash=False)

urlpatterns = [
    path(
        r"my/sent/",
        views.InquiresAPIView.as_view({"get": "get_my_sent_inquiries"}),
        name="my_sent_inquiries",
    ),
    path(
        r"my/contacts/",
        views.InquiresAPIView.as_view({"get": "get_my_contacts"}),
        name="my_inquiry_contacts",
    ),
    path(
        r"<uuid:recipient_profile_uuid>/send/",
        views.InquiresAPIView.as_view({"post": "send_inquiry"}),
        name="send_inquiry",
    ),
    path(
        r"my/received/",
        views.InquiresAPIView.as_view({"get": "get_my_received_inquiries"}),
        name="my_received_inquiries",
    ),
    path(
        r"my/meta-data/",
        views.InquiresAPIView.as_view({"get": "get_my_inquiry_data"}),
        name="my_inquiry_data",
    ),
    path(
        r"my/meta-data/update-contact/",
        views.InquiresAPIView.as_view({"post": "update_contact_data"}),
        name="update_contact_data",
    ),
    path(
        r"<int:request_id>/accept/",
        views.InquiresAPIView.as_view({"post": "accept_inquiry_request"}),
        name="accept_inquiry_request",
    ),
    path(
        r"<int:request_id>/reject/",
        views.InquiresAPIView.as_view({"post": "reject_inquiry_request"}),
        name="reject_inquiry_request",
    ),
]
