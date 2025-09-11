from django.urls import path
from rest_framework import routers

from profiles.api import views
from transfers.api import views

router = routers.SimpleRouter(trailing_slash=False)
router.register("", views.TransferStatusAPIView, basename="transfers")

urlpatterns = [
    path(
        r"<uuid:profile_uuid>/transfer-status/",
        views.TransferStatusAPIView.as_view({
            "get": "get_profile_transfer_status",
        }),
        name="profile_transfer_status",
    ),
    path(
        r"transfer-status/",
        views.TransferStatusAPIView.as_view({
            "patch": "update_profile_transfer_status",
            "post": "create_profile_transfer_status",
            "delete": "delete_profile_transfer_status",
        }),
        name="manage_transfer_status",
    ),
    path(
        r"list-transfer-status/",
        views.TransferStatusAPIView.as_view({
            "get": "list_transfer_status",
        }),
        name="list_transfer_status",
    ),
    path(
        r"transfer-status/additional-info/",
        views.TransferStatusAPIView.as_view({
            "get": "get_transfer_status_additional_info",
        }),
        name="list_transfer_status_additional_choices",
    ),
    path(
        r"<uuid:profile_uuid>/transfer-request/",
        views.TransferRequestAPIView.as_view({
            "get": "get_profile_transfer_request",
        }),
        name="profile_transfer_request",
    ),
    path(
        r"transfer-request/",
        views.TransferRequestAPIView.as_view({
            "post": "create_transfer_request",
            "patch": "update_transfer_request",
            "delete": "delete_profile_transfer_request",
        }),
        name="manage_transfer_request",
    ),
    path(
        r"transfer-request/status/",
        views.TransferRequestAPIView.as_view({
            "get": "list_transfer_request_status",
        }),
        name="list_transfer_request_status",
    ),
    path(
        r"transfer-request/number-of-trainings/",
        views.TransferRequestAPIView.as_view({
            "get": "list_transfer_request_number_of_trainings",
        }),
        name="list_transfer_request_number_of_trainings",
    ),
    path(
        r"transfer-request/benefits/",
        views.TransferRequestAPIView.as_view({
            "get": "list_transfer_request_benefits",
        }),
        name="list_transfer_request_benefits",
    ),
    path(
        r"transfer-request/salary/",
        views.TransferRequestAPIView.as_view({
            "get": "list_transfer_request_salary",
        }),
        name="list_transfer_request_salary",
    ),
    path(
        r"<uuid:profile_uuid>/transfer-request/teams/",
        views.TransferRequestAPIView.as_view({
            "get": "get_profile_actual_teams",
        }),
        name="list_transfer_request_actual_teams",
    ),
    #  Catalogues
    path(
        r"catalogue/transfer-request/",
        views.TransferRequestCatalogueAPIView.as_view({
            "get": "list_transfer_requests",
        }),
        name="list_transfer_request",
    ),
]
