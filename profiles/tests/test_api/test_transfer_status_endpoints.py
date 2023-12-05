import json

import factory
from django.db.models import signals
from django.urls import reverse
from requests import Response
from rest_framework.test import APIClient, APITestCase

from profiles.api.errors import TransferStatusDoesNotExistHTTPException
from profiles.models import BaseProfile, ProfileTransferStatus
from profiles.services import TransferStatusService
from utils.factories import (
    LeagueFactory,
    PlayerProfileFactory,
    TransferStatusFactory,
    UserFactory,
)
from utils.test.test_utils import MethodsNotAllowedTestsMixin, UserManager

transfer_service = TransferStatusService()


class TestTransferStatusAPI(APITestCase, MethodsNotAllowedTestsMixin):
    """Test transfer status API endpoints."""

    NOT_ALLOWED_METHODS = ["put"]

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def setUp(self):
        self.client = APIClient()
        user = UserFactory(password="test_password")
        self.profile: BaseProfile = PlayerProfileFactory.create(user=user)
        self.url = reverse(
            "api:profiles:profile_transfer_status",
            kwargs={"profile_uuid": self.profile.uuid},
        )

        self.user_manager = UserManager(self.client)
        self.headers = self.user_manager.custom_user_headers(
            email=user.email, password="test_password"
        )

    def test_list_transfer_statuses(self):
        """Test list transfer statuses. Expected status code 200."""
        response: Response = self.client.get(
            reverse("api:profiles:list_transfer_status")
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0

        expected_response = transfer_service.get_list_transfer_statutes()

        assert response.json() == expected_response

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_get_profile_no_transfer_status(self):
        """Test get profile transfer status. Expected status code 404."""
        response: Response = self.client.get(self.url, **self.headers)
        assert response.status_code == 404
        assert isinstance(response.json(), dict)
        assert (
            response.json().get("detail")
            == TransferStatusDoesNotExistHTTPException.default_detail
        )

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_get_profile_transfer_status(self):
        """Test get profile transfer status. Expected status code 200."""
        transfer_status_obj: ProfileTransferStatus = TransferStatusFactory.create(
            profile=self.profile
        )
        response: Response = self.client.get(self.url, **self.headers)

        assert response.status_code == 200
        assert isinstance(response.json(), dict)
        assert response.json().get(
            "status"
        ) == transfer_service.get_transfer_status_by_id(transfer_status_obj.status)

    def update_profile(self, new_data: dict) -> Response:
        """Patch request to update profile transfer status."""
        response: Response = self.client.patch(
            self.url,
            json.dumps(new_data),
            **self.headers,
        )
        return response

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_update_profile_transfer_status_email(self):
        """Test update profile transfer status. Expected status code 200."""
        transfer_status_obj: ProfileTransferStatus = TransferStatusFactory.create(
            profile=self.profile, contact_email=None
        )
        new_address_email = "test_email@test.test"
        response: Response = self.update_profile({"contact_email": new_address_email})

        assert response.status_code == 200
        assert isinstance(response.json(), dict)
        assert response.json().get("contact_email") == new_address_email

        transfer_status_obj.refresh_from_db()
        assert transfer_status_obj.contact_email == new_address_email

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_update_profile_transfer_status_phone(self):
        """Test update profile transfer status. Expected status code 200."""
        transfer_status_obj: ProfileTransferStatus = TransferStatusFactory.create(
            profile=self.profile, phone_number=None
        )
        new_contact_phone = "123456789"
        response: Response = self.update_profile(
            {"phone_number": {"number": new_contact_phone}}
        )

        assert response.status_code == 200
        assert isinstance(response.json(), dict)
        assert response.json().get("phone_number").get("number") == new_contact_phone

        transfer_status_obj.refresh_from_db()
        assert transfer_status_obj.phone_number == new_contact_phone

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_update_profile_transfer_status(self):
        """Test update profile transfer status. Expected status code 200."""
        transfer_status_obj: ProfileTransferStatus = TransferStatusFactory.create(
            profile=self.profile
        )
        new_status = transfer_service.get_list_transfer_statutes(id=2)[0]
        response: Response = self.update_profile({"status": 2})

        assert response.status_code == 200
        assert isinstance(response.json(), dict)
        assert response.json().get("status") == new_status

        transfer_status_obj.refresh_from_db()
        assert transfer_status_obj.status == new_status["id"]

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_update_profile_transfer_status_permission_denied(self):
        """Test update profile transfer status without permission."""
        user = UserFactory.create(password="test_password")
        self.headers = self.user_manager.custom_user_headers(
            email=user.email, password="test_password"
        )
        response: Response = self.client.patch(self.url, {"status": 2}, **self.headers)
        assert response.status_code == 403

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_update_profile_transfer_status_not_found(self):
        """
        Test update profile transfer status with no resource in DB.
        Expected status code 404.
        """
        response: Response = self.update_profile({"status": 2})

        assert response.status_code == 404
        assert isinstance(response.json(), dict)
        assert (
            response.json().get("detail")
            == TransferStatusDoesNotExistHTTPException.default_detail
        )

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_create_profile_transfer_status(self):
        """Test create profile transfer status. Expected status code 201."""
        league = LeagueFactory.create_league_as_highest_parent()
        data = {
            "status": 2,
            "league": [league.pk],
        }
        response: Response = self.client.post(
            self.url, json.dumps(data), **self.headers
        )

        assert response.status_code == 201
        assert isinstance(response.json(), dict)
        assert (
            response.json().get("status")
            == transfer_service.get_list_transfer_statutes(id=2)[0]
        )

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_create_profile_transfer_status_phone_num(self):
        """
        Test create profile transfer status with phone number.
        Expected status code 201.
        """
        league = LeagueFactory.create_league_as_highest_parent()
        data = {
            "status": 2,
            "league": [league.pk],
            "phone_number": {"dial_code": "+48", "number": "123456789"},
        }
        response: Response = self.client.post(
            self.url, json.dumps(data), **self.headers
        )

        assert response.status_code == 201
        assert response.json().get("phone_number").get("number") == "123456789"

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_create_profile_transfer_status_permission_denied(self):
        """Test create profile transfer status without permission."""
        user = UserFactory.create(password="test_password")
        self.headers = self.user_manager.custom_user_headers(
            email=user.email, password="test_password"
        )
        response: Response = self.client.post(
            self.url, json.dumps({"status": 2}), **self.headers
        )
        assert response.status_code == 403
