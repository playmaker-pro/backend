import json
from datetime import timedelta
from typing import Callable

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.client import RequestFactory
from django.urls import reverse
from django.utils import timezone
from requests import Response
from rest_framework.test import APIClient, APITestCase

from api.errors import PhoneNumberMustBeADictionaryHTTPException
from clubs.models import Team
from profiles.api.errors import (
    NotAOwnerOfTheTeamContributorHTTPException,
    TransferRequestDoesNotExistHTTPException,
    TransferStatusDoesNotExistHTTPException,
)
from profiles.api.serializers import PlayerPositionSerializer
from profiles.models import BaseProfile, PlayerPosition, TeamContributor
from profiles.services import (
    PlayerPositionService,
    TransferRequestService,
    TransferStatusService,
)
from profiles.tests.test_utils import set_stadion_address
from transfers.models import ProfileTransferRequest, ProfileTransferStatus
from utils import factories
from utils.factories import (
    LeagueFactory,
    PlayerProfileFactory,
    TeamContributorFactory,
    TransferRequestFactory,
    TransferStatusFactory,
    UserFactory,
)
from utils.factories.profiles_factories import ClubProfileFactory
from utils.test.test_utils import MethodsNotAllowedTestsMixin, UserManager

transfer_status_service = TransferStatusService()
transfer_request_service = TransferRequestService()

pytestmark = pytest.mark.django_db

GET_TRANSFER_STATUS_URL = lambda profile_uuid: reverse(
    "api:transfers:profile_transfer_status",
    kwargs={"profile_uuid": str(profile_uuid)},
)
GET_TRANSFER_REQUEST_URL = lambda profile_uuid: reverse(
    "api:transfers:profile_transfer_request",
    kwargs={"profile_uuid": str(profile_uuid)},
)


class TestTransferStatusAPI(APITestCase, MethodsNotAllowedTestsMixin):
    """Test transfer status API endpoints."""

    NOT_ALLOWED_METHODS = ["put"]

    def setUp(self):
        self.client = APIClient()
        user = UserFactory(password="test_password")
        self.profile: BaseProfile = PlayerProfileFactory.create(user=user)
        self.url = reverse(
            "api:transfers:manage_transfer_status",
        )
        self.get_url = GET_TRANSFER_STATUS_URL
        self.user_manager = UserManager(self.client)
        self.headers = self.user_manager.custom_user_headers(
            email=user.email, password="test_password"
        )

    def test_list_transfer_statuses(self):
        """Test list transfer statuses. Expected status code 200."""
        response: Response = self.client.get(
            reverse("api:transfers:list_transfer_status")
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0

        expected_response = transfer_status_service.get_list_transfer_statutes()

        assert response.json() == expected_response

    def test_get_profile_no_transfer_status(self):
        """Test get profile transfer status. Expected status code 404."""
        player = PlayerProfileFactory.create()
        response: Response = self.client.get(self.get_url(player.uuid), **self.headers)
        assert response.status_code == 404
        assert isinstance(response.json(), dict)
        assert (
            response.json().get("detail")
            == TransferStatusDoesNotExistHTTPException.default_detail
        )

    def test_get_profile_transfer_status(self):
        """Test get profile transfer status. Expected status code 200."""
        transfer_status_obj: ProfileTransferStatus = TransferStatusFactory.create(
            meta=self.profile.meta
        )
        response: Response = self.client.get(
            self.get_url(transfer_status_obj.meta.profile.uuid), **self.headers
        )

        assert response.status_code == 200
        assert isinstance(response.json(), dict)
        assert response.json().get(
            "status"
        ) == transfer_status_service.get_transfer_status_by_id(
            transfer_status_obj.status
        )
        assert response.status_code == 200

    def update_profile(self, new_data: dict) -> Response:
        """Patch request to update profile transfer status."""
        response: Response = self.client.patch(
            self.url,
            json.dumps(new_data),
            **self.headers,
        )
        return response

    def test_update_profile_transfer_status(self):
        """Test update profile transfer status. Expected status code 200."""
        transfer_status_obj: ProfileTransferStatus = TransferStatusFactory.create(
            meta=self.profile.meta
        )
        new_status = transfer_status_service.get_list_transfer_statutes(id=2)[0]
        response: Response = self.update_profile({"status": 2})

        assert response.status_code == 200
        assert isinstance(response.json(), dict)
        assert response.json().get("status") == new_status

        transfer_status_obj.refresh_from_db()
        assert transfer_status_obj.status == new_status["id"]

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

    def test_create_profile_transfer_status(self):
        """Test create profile transfer status. Expected status code 201."""
        league = LeagueFactory.create_league_as_highest_parent()
        data = {
            "contact_email": "contact@email.com",
            "phone_number": {"dial_code": 48, "number": "+111222333"},
            "status": 1,
            "additional_info": [1],
            "league": [league.pk],
        }
        response: Response = self.client.post(
            self.url, json.dumps(data), **self.headers
        )

        assert response.status_code == 201
        assert isinstance(response.json(), dict)
        assert (
            response.json().get("status")
            == transfer_status_service.get_list_transfer_statutes(id=1)[0]
        )

    def test_create_profile_transfer_status_without_benefits(self):
        """Test create profile transfer status. Expected status code 201."""
        league = LeagueFactory.create_league_as_highest_parent()
        data = {
            "contact_email": "contact@email.com",
            "phone_number": {"dial_code": 48, "number": "+111222333"},
            "status": 1,
            "league": [league.pk],
        }
        response: Response = self.client.post(
            self.url, json.dumps(data), **self.headers
        )

        assert response.status_code == 201
        assert isinstance(response.json(), dict)
        assert (
            response.json().get("status")
            == transfer_status_service.get_list_transfer_statutes(id=1)[0]
        )

    def test_transfer_status_with_extra_fields(self):
        """
        Test create profile transfer status with extra fields.
        Expected status code 201.
        """
        league = LeagueFactory.create_league_as_highest_parent()
        data = {
            "status": 2,
            "league": [league.pk],
            "additional_info": [1],
            "number_of_trainings": 1,
            "salary": 1,
        }
        response: Response = self.client.post(
            self.url, json.dumps(data), **self.headers
        )

        assert response.status_code == 201
        for element in data.keys():
            assert element in response.json()

    def test_get_my_transfer_status(self):
        """Test get my transfer status. Expected status code 200."""
        transfer_status_obj: ProfileTransferStatus = TransferStatusFactory.create(
            meta=self.profile.meta, is_anonymous=True
        )
        response: Response = self.client.get(
            self.get_url(transfer_status_obj.meta.profile.uuid), **self.headers
        )

        assert response.status_code == 200
        assert "status" in response.json()


class TestTransferRequestAPI(APITestCase, MethodsNotAllowedTestsMixin):
    """Test transfer request API endpoints."""

    NOT_ALLOWED_METHODS = ["put"]

    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory(password="test_password")
        self.profile: BaseProfile = PlayerProfileFactory.create(user=self.user)
        self.url = reverse(
            "api:transfers:manage_transfer_request",
        )
        self.get_url = GET_TRANSFER_REQUEST_URL
        self.user_manager = UserManager(self.client)
        self.headers = self.user_manager.custom_user_headers(
            email=self.user.email, password="test_password"
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
            "position": [player_position1.pk, player_position2.pk],
            "benefits": [2, 4],
            "number_of_trainings": 1,
            "salary": 1,
            "contact_email": "dwdw@fefe.com",
            "phone_number": {"dial_code": 2, "number": "1234567"},
        }

    def test_list_transfer_request_statuses(self):
        """Test list transfer statuses. Expected status code 200."""
        response: Response = self.client.get(
            reverse("api:transfers:list_transfer_request_status")
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0

        expected_response = transfer_request_service.get_list_transfer_statutes()
        assert response.json() == expected_response

    def test_list_transfer_request_num_of_trainings(self):
        """Test list transfer number of trainings. Expected status code 200."""
        response: Response = self.client.get(
            reverse("api:transfers:list_transfer_request_number_of_trainings")
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0

        expected_response = (
            transfer_request_service.get_list_transfer_num_of_trainings()
        )

        assert response.json() == expected_response

    def test_list_transfer_request_benefits(self):
        """Test list transfer additional information. Expected status code 200."""
        response: Response = self.client.get(
            reverse("api:transfers:list_transfer_request_benefits")
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0

        expected_response = transfer_request_service.get_list_transfer_additional_info()

        assert response.json() == expected_response

    def test_list_transfer_request_salary(self):
        """Test list transfer request salary. Expected status code 200."""
        response: Response = self.client.get(
            reverse("api:transfers:list_transfer_request_salary")
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0

        expected_response = transfer_request_service.get_list_transfer_salary()

        assert response.json() == expected_response

    def test_get_profile_no_transfer_request(self):
        """
        Test get profile transfer request. Expected status code 404,
        because profile has no transfer request.
        """
        response: Response = self.client.get(
            self.get_url(self.profile.uuid), **self.headers
        )
        assert response.status_code == 404
        assert isinstance(response.json(), dict)
        assert (
            response.json().get("detail")
            == TransferRequestDoesNotExistHTTPException.default_detail
        )

    def test_get_profile_transfer_request(self):
        """
        Test GET profile transfer request and check if response data is correct.
        Expected status code 200.
        """
        TeamContributorFactory.create(profile_uuid=self.profile.uuid)
        transfer_request_obj: ProfileTransferRequest = TransferRequestFactory.create(
            meta=self.profile.meta
        )
        response: Response = self.client.get(
            self.get_url(self.profile.uuid), **self.headers
        )

        assert response.status_code == 200
        assert isinstance(response.json(), dict)

        expected_status = transfer_request_service.get_transfer_request_status_by_id(
            transfer_request_obj.status
        )
        assert response.json().get("status") == expected_status

        expected_positions = []
        for position in transfer_request_obj.position.all():
            expected_positions.append(PlayerPositionSerializer(position).data)

        assert response.json().get("position") == expected_positions

        expected_trainings = transfer_request_service.get_num_of_trainings_by_id(
            transfer_request_obj.number_of_trainings
        )
        assert response.json().get("number_of_trainings") == expected_trainings

        expected_infos = []
        for element in transfer_request_obj.benefits:
            expected_infos.append(
                transfer_request_service.get_additional_info_by_id(element)
            )
        assert response.json().get("benefits") == expected_infos

        expected_salary = transfer_request_service.get_salary_by_id(
            transfer_request_obj.salary
        )

        assert response.json().get("salary") == expected_salary

    def update_profile_transfer_request(self, new_data: dict) -> Response:
        """Patch request to update profile transfer status."""
        response: Response = self.client.patch(
            self.url,
            json.dumps(new_data),
            **self.headers,
        )
        return response

    def test_get_my_transfer_request(self):
        TeamContributorFactory.create(profile_uuid=self.profile.uuid)
        transfer_request_obj: ProfileTransferRequest = TransferRequestFactory.create(
            meta=self.profile.meta, is_anonymous=True
        )

        response: Response = self.client.get(
            self.get_url(transfer_request_obj.meta.profile.uuid), **self.headers
        )
        assert response.status_code == 200
        assert "status" in response.json()

    # @factory.django.mute_signals(signals.pre_save, signals.post_save)
    # def test_update_profile_transfer_request_email(self):
    #     """Test update profile transfer request. Expected status code 200."""
    #     self.profile.user.userpreferences.contact_email = None
    #     self.profile.user.userpreferences.save()
    #     transfer_request_obj: ProfileTransferRequest = TransferRequestFactory.create(
    #         profile=self.profile
    #     )
    #     new_address_email = "test_email@test.test"
    #     response: Response = self.update_profile_transfer_request(
    #         {"contact_email": new_address_email}
    #     )

    #     assert response.status_code == 200
    #     assert isinstance(response.json(), dict)
    #     assert response.json().get("contact_email") == new_address_email

    #     transfer_request_obj.profile.user.userpreferences.refresh_from_db()
    #     assert (
    #         transfer_request_obj.profile.user.userpreferences.contact_email
    #         == new_address_email
    #     )

    # @factory.django.mute_signals(signals.pre_save, signals.post_save)
    # def test_update_profile_transfer_request_phone(self):
    #     """Test update profile transfer request. Expected status code 200."""
    #     self.profile.user.userpreferences.phone_number = None
    #     self.profile.user.userpreferences.dial_code = None
    #     self.profile.user.userpreferences.save()
    #     transfer_request_obj: ProfileTransferRequest = TransferRequestFactory.create(
    #         profile=self.profile
    #     )
    #     new_contact_phone = "123456789"
    #     response: Response = self.update_profile_transfer_request(
    #         {"phone_number": {"number": new_contact_phone}}
    #     )

    #     assert response.status_code == 200
    #     assert isinstance(response.json(), dict)
    #     assert response.json().get("phone_number").get("number") == new_contact_phone

    #     transfer_request_obj.refresh_from_db()
    #     assert (
    #         transfer_request_obj.profile.user.userpreferences.phone_number
    #         == new_contact_phone
    #     )

    def test_update_profile_transfer_request_status(self):
        """Test update profile transfer request. Expected status code 200."""
        TeamContributorFactory.create(profile_uuid=self.profile.uuid)
        transfer_status_obj: ProfileTransferRequest = TransferRequestFactory.create(
            meta=self.profile.meta
        )
        new_status: dict = transfer_request_service.get_transfer_request_status_by_id(
            transfer_status_id=2
        )
        response: Response = self.update_profile_transfer_request({"status": 2})
        assert response.status_code == 200
        assert isinstance(response.json(), dict)
        assert response.json().get("status") == new_status

        transfer_status_obj.refresh_from_db()
        assert transfer_status_obj.status == new_status["id"]

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

    def test_create_profile_transfer_request_full_data(self):
        """Test create profile transfer status. Expected status code 201."""
        response: Response = self.client.post(
            self.url, json.dumps(self.data), **self.headers
        )

        assert response.status_code == 201
        assert isinstance(response.json(), dict)

        expected_status = transfer_request_service.get_transfer_request_status_by_id(
            transfer_status_id=1
        )
        assert response.json().get("status") == expected_status

    def test_create_profile_transfer_request_without_additional_info(self):
        """Test create profile transfer status. Expected status code 201."""
        self.data.pop("benefits")
        response: Response = self.client.post(
            self.url, json.dumps(self.data), **self.headers
        )

        assert response.status_code == 201
        assert isinstance(response.json(), dict)
        expected_status = transfer_request_service.get_transfer_request_status_by_id(
            transfer_status_id=1
        )
        assert response.json().get("status") == expected_status

    def test_delete_profile_transfer_request(self):
        """Test delete profile transfer status. Expected status code 204."""
        tc = TeamContributorFactory.create(
            profile_uuid=self.profile.uuid,
        )
        transfer_request_obj: ProfileTransferRequest = TransferRequestFactory.create(
            meta=self.profile.meta
        )
        response: Response = self.client.delete(self.url, **self.headers)

        assert response.status_code == 204
        assert response.content == b""

        with pytest.raises(ProfileTransferRequest.DoesNotExist):
            transfer_request_obj.refresh_from_db()

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

    def test_create_transfer_request_without_team_contributor(self):
        """
        Test create profile transfer status without team contributor.
        Expected status code 400.
        """
        self.data.pop("requesting_team")
        response: Response = self.client.post(
            self.url, json.dumps(self.data), **self.headers
        )

        assert response.status_code == 201
        assert isinstance(response.json(), dict)
        assert "requesting_team" in response.json()
        assert self.user.profile.meta.transfer_object.requesting_team is None


def test_profile_transfer_request_teams_endpoint(
    api_client: APIClient,
    user_factory_fixture: Callable,
    uploaded_file: SimpleUploadedFile,
):
    """
    Test profile transfer request teams endpoint. Expected status code 200 and
    correct response data.
    """
    p1 = ClubProfileFactory.create()
    url = reverse(
        "api:transfers:list_transfer_request_actual_teams",
        kwargs={"profile_uuid": p1.uuid},
    )
    api_client.force_authenticate(user=p1.user)
    team_contributor1: TeamContributor = TeamContributorFactory.create(
        profile_uuid=p1.uuid
    )
    team_contributor2: TeamContributor = TeamContributorFactory.create(
        profile_uuid=p1.uuid
    )
    team1: Team = team_contributor1.team_history.first()
    team2: Team = team_contributor2.team_history.first()
    team1.club.picture.save(uploaded_file.name, uploaded_file, save=True)
    team2.club.picture.save(uploaded_file.name, uploaded_file, save=True)

    request = RequestFactory().get("/your-endpoint-url/")

    expected_response = [
        {
            "id": team_contributor1.pk,
            "round": team_contributor1.round,
            "team": {
                "id": team1.pk,
                "team_name": team1.name,
                "league_name": team1.league_history.league.name,  # noqa: E501
                "league_id": team1.league_history.league.pk,
                "team_contributor_id": None,
                "picture_url": request.build_absolute_uri(team1.get_club_pic),
                "country": team1.get_country,
                "season": team1.league_history.season.name,
            },
        },
        {
            "id": team_contributor2.pk,
            "round": team_contributor2.round,
            "team": {
                "id": team2.pk,
                "team_name": team2.name,
                "league_name": team2.league_history.league.name,  # noqa: E501
                "league_id": team2.league_history.league.pk,
                "team_contributor_id": None,
                "picture_url": request.build_absolute_uri(team2.get_club_pic),
                "country": team2.get_country,
                "season": team2.league_history.season.name,
            },
        },
    ]
    response: Response = api_client.get(url)
    assert response.json() == expected_response


class TestTransferRequestCatalogue:
    url = reverse("api:transfers:list_transfer_request")

    def test_localization_filter(self, api_client) -> None:
        """Test localization filter."""
        start_latitude, start_longitude = 54.25451551801814, 18.315362070454498

        # Create three transfer requests
        profile_a = factories.ClubProfileFactory()
        profile_b = factories.ClubProfileFactory()
        profile_c = factories.ClubProfileFactory()
        t1 = TransferRequestFactory.create(
            meta=profile_a.meta,
        )
        t2 = TransferRequestFactory.create(
            meta=profile_b.meta,
        )
        t3 = TransferRequestFactory.create(
            meta=profile_c.meta,
        )
        # Set latitude and longitude for each team's stadion address
        set_stadion_address(t1, start_latitude, start_longitude)
        set_stadion_address(t2, 54.21354701964793, 18.36439364315754)
        set_stadion_address(t3, 54.13695015319587, 18.458313275377453)

        # Test with radius = 2 km
        response = api_client.get(
            self.url,
            {"latitude": start_latitude, "longitude": start_longitude, "radius": 2},
        )

        assert len(response.data["results"]) == 1

        # Test with radius = 10 km
        response = api_client.get(
            self.url,
            {"latitude": start_latitude, "longitude": start_longitude, "radius": 10},
        )
        assert len(response.data["results"]) == 2

        # Test with radius = 20 km
        response = api_client.get(
            self.url,
            {"latitude": start_latitude, "longitude": start_longitude, "radius": 20},
        )
        assert len(response.data["results"]) == 3


class TestAnonymousTransferStatus:
    url_path = "api:transfers:manage_transfer_status"

    @pytest.fixture
    def profile(self, player_profile: BaseProfile) -> BaseProfile:
        """Create a profile for testing."""
        return player_profile

    @pytest.fixture
    def payload(self) -> dict:
        """Create a payload for testing."""
        return {
            "contact_email": "contact@email.com",
            "phone_number": {"dial_code": 48, "number": "+111222333"},
            "status": 1,
            "additional_info": [1],
            "league": [LeagueFactory.create_league_as_highest_parent().pk],
            "is_anonymous": True,
        }

    def _list_transfer_statuses(self, api_client: APIClient) -> Response:
        """Helper method to list transfer statuses."""
        return api_client.get(
            reverse("api:profiles:create_or_list_profiles"),
            {"role": "P", "transfer_status": "1"},
        )

    def test_create_anonymous_transfer_status_full_flow(
        self, profile, api_client, payload
    ):
        assert not ProfileTransferStatus.objects.filter().exists()
        profile.setup_premium_profile()
        api_client.force_authenticate(profile.user)
        response: Response = api_client.post(
            reverse(self.url_path),
            payload,
            format="json",
        )

        assert response.status_code == 201

        assert ProfileTransferStatus.objects.filter().exists()

        profile.refresh_from_db()
        obj = profile.meta.transfer_object

        assert obj.is_anonymous
        assert obj.anonymous_uuid is not None

        # Check if is listed in transfer status list
        list_profiles_response = self._list_transfer_statuses(api_client)
        data = list_profiles_response.json()

        assert list_profiles_response.status_code == 200
        assert data["count"] == 1

        obj_data = data["results"][0]

        assert obj_data["slug"] == f"anonymous-{obj.anonymous_uuid}"
        assert obj_data["uuid"] == str(obj.anonymous_uuid)
        assert obj_data["user"]["id"] == 0
        assert obj_data["user"]["first_name"] == "Anonimowy"
        assert obj_data["user"]["last_name"] == "profil"
        assert obj_data["user"]["picture"] is None
        assert obj_data["team_history_object"] is None

        response = api_client.patch(
            reverse(self.url_path),
            {
                "is_anonymous": False,
            },
            format="json",
        )
        profile.refresh_from_db()

        assert response.json()["is_anonymous"] is False
        assert profile.meta.transfer_object.is_anonymous is False

        response = api_client.patch(
            reverse(self.url_path),
            {
                "is_anonymous": True,
            },
            format="json",
        )
        profile.refresh_from_db()

        assert profile.meta.transfer_object.is_anonymous is True

        # Simulate premium expired
        premium = profile.premium
        premium.valid_until = timezone.now() - timedelta(days=1)
        premium.save()

        assert profile.is_premium is False

        # Should not be listed in transfer status list
        list_profiles_response = self._list_transfer_statuses(api_client)
        data = list_profiles_response.json()

        assert list_profiles_response.status_code == 200
        assert data["count"] == 1

        # Transfer status should not be anonymous anymore
        assert not profile.meta.transfer_object.is_anonymous

    def test_cannot_create_anonymous_transfer_status_without_premium(
        self, profile, api_client, payload
    ):
        """
        Test that anonymous transfer status cannot be created without premium.
        Expected status code 403.
        """
        assert not ProfileTransferStatus.objects.filter().exists()
        api_client.force_authenticate(profile.user)
        response: Response = api_client.post(
            reverse(self.url_path),
            payload,
            format="json",
        )

        assert response.status_code == 400
        assert not ProfileTransferStatus.objects.filter().exists()

    # def test_expose_anonymous_transfer_status(self, profile, api_client, payload):
    #     profile.setup_premium_profile()
    #     transfer_status = TransferStatusFactory.create(
    #         status="1", meta=profile.meta, is_anonymous=True
    #     )
    #     api_client.force_authenticate(profile.user)
    #     response = api_client.get(
    #         GET_TRANSFER_STATUS_URL(transfer_status.anonymous_uuid),
    #         {"is_anonymous": True, "expose": True},
    #         format="json",
    #     )

    #     assert response.status_code == 200


class TestAnonymousTransferRequest:
    url_path = "api:transfers:manage_transfer_request"

    @pytest.fixture
    def payload(self) -> dict:
        """Create a payload for testing."""
        return {  # add "requesting_team" later
            "gender": "M",
            "status": 1,
            "position": [
                PlayerPosition.objects.first().pk,
                PlayerPosition.objects.last().pk,
            ],
            "benefits": [2, 4],
            "number_of_trainings": 1,
            "salary": 1,
            "contact_email": "dwdw@fefe.com",
            "phone_number": {"dial_code": 2, "number": "1234567"},
            "is_anonymous": True,
        }

    def test_create_anonymous_transfer_request_full_flow_for_coach(
        self, coach_profile, api_client, payload
    ):
        """Test that Coach cannot use anonymous mode (only Clubs and Players can)."""
        assert not ProfileTransferRequest.objects.filter().exists()
        coach_profile.setup_premium_profile()
        api_client.force_authenticate(coach_profile.user)
        payload["requesting_team"] = TeamContributorFactory.create(
            profile_uuid=coach_profile.uuid
        ).pk
        response = api_client.post(
            reverse(self.url_path),
            payload,
            format="json",
        )

        # Coaches cannot use anonymous mode - should get 400 validation error
        assert response.status_code == 400
        assert "Anonymous profile is only available for clubs and players" in str(response.content)
        assert not ProfileTransferRequest.objects.filter().exists()

    def test_expose_anonymous_transfer_request(self, coach_profile, api_client):
        """
        Test that anonymous transfer request can be exposed.
        Expected status code 200.
        """
        coach_profile.setup_premium_profile()
        transfer_request = TransferRequestFactory.create(
            meta=coach_profile.meta, is_anonymous=True
        )
        api_client.force_authenticate(coach_profile.user)
        response = api_client.get(
            GET_TRANSFER_REQUEST_URL(transfer_request.anonymous_uuid),
            {"is_anonymous": True, "expose": True},
            format="json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["requesting_team"]["id"] != 0
        assert data["requesting_team"]["team"]["team_name"] != "Anonimowa drużyna"
        assert data["requesting_team"]["team"]["id"] != 0
        assert data["profile_uuid"] == str(coach_profile.uuid)
        # Contact fields are now write-only and never appear in responses
        assert "phone_number" not in data
        assert "contact_email" not in data

    def test_expose_anonymous_transfer_request_error_not_owner(
        self, coach_profile, player_profile, api_client
    ):
        """
        Test that anonymous transfer request can be exposed.
        Expected status code 200.
        """
        coach_profile.setup_premium_profile()
        transfer_request = TransferRequestFactory.create(
            meta=coach_profile.meta, is_anonymous=True
        )
        api_client.force_authenticate(player_profile.user)
        response = api_client.get(
            GET_TRANSFER_REQUEST_URL(transfer_request.anonymous_uuid),
            {"is_anonymous": True, "expose": True},
            format="json",
        )

        assert response.status_code == 400
        assert response.json() == {
            "error": "Must be owner of the profile to expose anonymous transfer request"
        }
