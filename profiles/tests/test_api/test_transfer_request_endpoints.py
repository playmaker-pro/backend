import json
from typing import Callable

import factory
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import signals
from django.test.client import RequestFactory
from django.urls import reverse
from requests import Response
from rest_framework.test import APIClient, APITestCase

from clubs.models import Team
from profiles.api.errors import (
    NotAOwnerOfTheTeamContributorHTTPException,
    PhoneNumberMustBeADictionaryHTTPException,
    TransferRequestDoesNotExistHTTPException,
)
from profiles.api.serializers import PlayerPositionSerializer
from profiles.models import BaseProfile, ProfileTransferRequest, TeamContributor
from profiles.schemas import TransferRequestSchema
from profiles.services import PlayerPositionService, TransferRequestService
from utils.factories import (
    PlayerProfileFactory,
    TeamContributorFactory,
    TransferRequestFactory,
    UserFactory,
)
from utils.test.test_utils import MethodsNotAllowedTestsMixin, UserManager

transfer_service = TransferRequestService()


class TestTransferRequestAPI(APITestCase, MethodsNotAllowedTestsMixin):
    """Test transfer request API endpoints."""

    NOT_ALLOWED_METHODS = ["put"]

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def setUp(self):
        self.client = APIClient()
        user = UserFactory(password="test_password")
        self.profile: BaseProfile = PlayerProfileFactory.create(user=user)
        self.url = reverse(
            "api:profiles:profile_transfer_request",
            kwargs={"profile_uuid": self.profile.uuid},
        )

        self.user_manager = UserManager(self.client)
        self.headers = self.user_manager.custom_user_headers(
            email=user.email, password="test_password"
        )
        team_contributor: TeamContributor = TeamContributorFactory.create(
            profile_uuid=self.profile.uuid
        )
        position_service = PlayerPositionService()
        position_service.start_position_cleanup_process()

        player_position1 = position_service.all().first()
        player_position2 = position_service.all().last()
        self.data = {
            "requesting_team": team_contributor.pk,
            "gender": "M",
            "status": 1,
            "player_position": [player_position1.pk, player_position2.pk],
            "benefits": [2, 4],
            "number_of_trainings": 1,
            "salary": 1,
            "contact_email": "dwdw@fefe.com",
            "phone_number": {"dial_code": 2, "number": "1234567"},
        }

    def test_list_transfer_request_statuses(self):
        """Test list transfer statuses. Expected status code 200."""
        response: Response = self.client.get(
            reverse("api:profiles:list_transfer_request_status")
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0

        expected_response = transfer_service.get_list_transfer_statutes()
        assert response.json() == expected_response

    def test_list_transfer_request_num_of_trainings(self):
        """Test list transfer number of trainings. Expected status code 200."""
        response: Response = self.client.get(
            reverse("api:profiles:list_transfer_request_number_of_trainings")
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0

        expected_response = transfer_service.get_list_transfer_num_of_trainings()

        assert response.json() == expected_response

    def test_list_transfer_request_benefits(self):
        """Test list transfer additional information. Expected status code 200."""
        response: Response = self.client.get(
            reverse("api:profiles:list_transfer_request_benefits")
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0

        expected_response = transfer_service.get_list_transfer_additional_info()

        assert response.json() == expected_response

    def test_list_transfer_request_salary(self):
        """Test list transfer request salary. Expected status code 200."""
        response: Response = self.client.get(
            reverse("api:profiles:list_transfer_request_salary")
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0

        expected_response = transfer_service.get_list_transfer_salary()

        assert response.json() == expected_response

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_get_profile_no_transfer_request(self):
        """
        Test get profile transfer request. Expected status code 404,
        because profile has no transfer request.
        """
        response: Response = self.client.get(self.url, **self.headers)
        assert response.status_code == 404
        assert isinstance(response.json(), dict)
        assert (
            response.json().get("detail")
            == TransferRequestDoesNotExistHTTPException.default_detail
        )

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_get_profile_transfer_request(self):
        """
        Test GET profile transfer request and check if response data is correct.
        Expected status code 200.
        """
        transfer_request_obj: ProfileTransferRequest = TransferRequestFactory.create(
            profile=self.profile
        )
        response: Response = self.client.get(self.url, **self.headers)

        assert response.status_code == 200
        assert isinstance(response.json(), dict)

        expected_status = transfer_service.get_transfer_request_status_by_id(
            transfer_request_obj.status
        )
        assert response.json().get("status") == expected_status

        expected_positions = []
        for position in transfer_request_obj.player_position.all():
            expected_positions.append(PlayerPositionSerializer(position).data)

        assert response.json().get("player_position") == expected_positions

        expected_trainings = transfer_service.get_num_of_trainings_by_id(
            transfer_request_obj.number_of_trainings
        )
        assert response.json().get("number_of_trainings") == expected_trainings

        expected_infos = []
        for element in transfer_request_obj.benefits:
            expected_infos.append(transfer_service.get_additional_info_by_id(element))
        assert response.json().get("benefits") == expected_infos

        expected_salary = transfer_service.get_salary_by_id(transfer_request_obj.salary)
        assert response.json().get("salary") == expected_salary

        data = response.json()
        fields_schema = list(TransferRequestSchema.__fields__.keys())

        for field in fields_schema:
            assert field in list(data.keys())

    def update_profile_transfer_request(self, new_data: dict) -> Response:
        """Patch request to update profile transfer status."""
        response: Response = self.client.patch(
            self.url,
            json.dumps(new_data),
            **self.headers,
        )
        return response

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_update_profile_transfer_request_email(self):
        """Test update profile transfer request. Expected status code 200."""
        transfer_request_obj: ProfileTransferRequest = TransferRequestFactory.create(
            profile=self.profile, contact_email=None
        )
        new_address_email = "test_email@test.test"
        response: Response = self.update_profile_transfer_request(
            {"contact_email": new_address_email}
        )

        assert response.status_code == 200
        assert isinstance(response.json(), dict)
        assert response.json().get("contact_email") == new_address_email

        transfer_request_obj.refresh_from_db()
        assert transfer_request_obj.contact_email == new_address_email

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_update_profile_transfer_request_phone(self):
        """Test update profile transfer request. Expected status code 200."""
        transfer_request_obj: ProfileTransferRequest = TransferRequestFactory.create(
            profile=self.profile, phone_number=None
        )
        new_contact_phone = "123456789"
        response: Response = self.update_profile_transfer_request(
            {"phone_number": {"number": new_contact_phone}}
        )

        assert response.status_code == 200
        assert isinstance(response.json(), dict)
        assert response.json().get("phone_number").get("number") == new_contact_phone

        transfer_request_obj.refresh_from_db()
        assert transfer_request_obj.phone_number == new_contact_phone

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_update_profile_transfer_request_status(self):
        """Test update profile transfer request. Expected status code 200."""
        transfer_status_obj: ProfileTransferRequest = TransferRequestFactory.create(
            profile=self.profile
        )
        new_status: dict = transfer_service.get_transfer_request_status_by_id(
            transfer_status_id=2
        )
        response: Response = self.update_profile_transfer_request({"status": 2})

        assert response.status_code == 200
        assert isinstance(response.json(), dict)
        assert response.json().get("status") == new_status

        transfer_status_obj.refresh_from_db()
        assert transfer_status_obj.status == new_status["id"]

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_update_profile_transfer_request_permission_denied(self):
        """Test update profile transfer status without permission."""
        user = UserFactory.create(password="test_password")
        self.headers = self.user_manager.custom_user_headers(
            email=user.email, password="test_password"
        )
        response: Response = self.client.patch(self.url, {"status": 2}, **self.headers)
        assert response.status_code == 403

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_update_profile_transfer_request_not_found(self):
        """
        Test update profile transfer status with no resource in DB.
        Expected status code 404.
        """
        response: Response = self.update_profile_transfer_request({"status": 2})
        assert response.status_code == 404
        assert isinstance(response.json(), dict)
        assert (
            response.json().get("detail")
            == TransferRequestDoesNotExistHTTPException.default_detail
        )

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_create_profile_transfer_request_not_a_owner_of_the_team(self):
        """Test create profile transfer status. Expected status code 403."""
        team_contributor: TeamContributor = TeamContributorFactory.create()
        self.data["requesting_team"] = team_contributor.pk

        response: Response = self.client.post(
            self.url, json.dumps(self.data), **self.headers
        )

        assert response.status_code == 403
        assert isinstance(response.json(), dict)

        assert (
            response.json().get("detail")
            == NotAOwnerOfTheTeamContributorHTTPException.default_detail
        )

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_create_profile_transfer_request_full_data(self):
        """Test create profile transfer status. Expected status code 201."""
        response: Response = self.client.post(
            self.url, json.dumps(self.data), **self.headers
        )

        assert response.status_code == 201
        assert isinstance(response.json(), dict)

        expected_status = transfer_service.get_transfer_request_status_by_id(
            transfer_status_id=1
        )
        assert response.json().get("status") == expected_status

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_create_profile_transfer_request_without_additional_info(self):
        """Test create profile transfer status. Expected status code 201."""
        self.data.pop("benefits")
        response: Response = self.client.post(
            self.url, json.dumps(self.data), **self.headers
        )

        assert response.status_code == 201
        assert isinstance(response.json(), dict)
        expected_status = transfer_service.get_transfer_request_status_by_id(
            transfer_status_id=1
        )
        assert response.json().get("status") == expected_status

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

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_delete_profile_transfer_request(self):
        """Test delete profile transfer status. Expected status code 204."""
        transfer_request_obj: ProfileTransferRequest = TransferRequestFactory.create(
            profile=self.profile
        )
        response: Response = self.client.delete(self.url, **self.headers)

        assert response.status_code == 204
        assert response.content == b""

        with pytest.raises(ProfileTransferRequest.DoesNotExist):
            transfer_request_obj.refresh_from_db()

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_create_object_passing_wrong_phone_number(self):
        """
        Test create profile transfer status with wrong phone number.
        Expected status code 400.
        """
        self.data["phone_number"] = 123
        response: Response = self.client.post(
            self.url, json.dumps(self.data), **self.headers
        )

        assert response.status_code == 400
        assert isinstance(response.json(), dict)
        expected_response = PhoneNumberMustBeADictionaryHTTPException.default_detail
        assert response.json().get("detail") == expected_response


@pytest.mark.django_db
def test_profile_transfer_request_teams_endpoint(
    api_client: APIClient,
    user_factory_fixture: Callable,
    uploaded_file: SimpleUploadedFile,
    mute_signals,
):
    """
    Test profile transfer request teams endpoint. Expected status code 200 and
    correct response data.
    """
    user = user_factory_fixture(password="test_password")
    profile: BaseProfile = PlayerProfileFactory.create(user=user)
    url = reverse(
        "api:profiles:list_transfer_request_actual_teams",
        kwargs={"profile_uuid": profile.uuid},
    )

    user_manager = UserManager(api_client)
    headers = user_manager.custom_user_headers(
        email=user.email, password="test_password"
    )

    team_contributor1: TeamContributor = TeamContributorFactory.create(
        profile_uuid=profile.uuid
    )
    team_contributor2: TeamContributor = TeamContributorFactory.create(
        profile_uuid=profile.uuid
    )

    team1: Team = team_contributor1.team_history.first()
    team2: Team = team_contributor2.team_history.first()

    league = team1.league_history.league
    league.save()

    league2 = team2.league_history.league
    league2.save()

    team1.club.picture.save(uploaded_file.name, uploaded_file, save=True)
    team2.club.picture.save(uploaded_file.name, uploaded_file, save=True)

    request = RequestFactory().get("/your-endpoint-url/")

    expected_response = [
        {
            "id": team_contributor1.pk,
            "round": team_contributor1.round,
            "is_primary": team_contributor1.is_primary,
            "is_primary_for_round": team_contributor1.is_primary_for_round,
        },
        {
            "id": team_contributor2.pk,
            "team_id": team2.pk,
            "picture_url": request.build_absolute_uri(team2.get_club_pic),
            "team_name": team2.name,
            "league_name": team2.league_history.league.name,
            "league_id": team2.league_history.league.pk,
            "season_name": team2.league_history.season.name,
            "round": team_contributor2.round,
        },
    ]

    response: Response = api_client.get(url, **headers)
    assert response.json() == expected_response
