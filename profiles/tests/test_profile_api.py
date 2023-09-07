import json
import uuid

import pytest
from django.urls import reverse
from parameterized import parameterized
from rest_framework.test import APIClient, APITestCase

from profiles.services import ProfileService
from profiles.tests import utils
from roles.definitions import CLUB_ROLE_TEAM_LEADER
from utils import factories
from utils.test.test_utils import UserManager

profile_service = ProfileService()


class TestGetProfileAPI(APITestCase):
    def setUp(self) -> None:
        """set up object factories"""
        self.client: APIClient = APIClient()
        self.user = UserManager(self.client)
        self.user_obj = self.user.create_superuser()
        self.headers = self.user.get_headers()
        factories.UserFactory.create_batch_force_order(5)
        factories.ClubFactory(id=1)
        factories.TeamHistoryFactory(
            team=factories.TeamFactory(name="Drużyna FC II", id=1), id=1
        )
        self.url = "api:profiles:get_profile"

    def test_get_profile_valid_without_authentication(self) -> None:
        """correct get request with valid uuid, no need to authenticate"""
        profile_uuid = factories.PlayerProfileFactory.create(user_id=1).uuid
        response = self.client.get(
            reverse(self.url, kwargs={"profile_uuid": profile_uuid}), **self.headers
        )
        assert response.status_code == 200

    def test_get_profile_invalid(self) -> None:
        """get request shouldn't pass with fake uuid"""
        fake_uuid = uuid.uuid4()
        response = self.client.get(
            reverse(self.url, kwargs={"profile_uuid": fake_uuid}), **self.headers
        )
        assert response.status_code == 404


class TestCreateUpdateProfileAPI(APITestCase):
    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.manager = UserManager(self.client)
        self.user_obj = self.manager.create_superuser()
        self.headers = self.manager.get_headers()
        factories.ClubFactory(id=1)
        factories.TeamHistoryFactory(
            team=factories.TeamFactory(name="Drużyna FC II", id=1), id=1
        )
        self.url = reverse("api:profiles:get_create_or_update_profile")

    @parameterized.expand(
        [
            [{"role": "Piłkarz"}],
            [{"role": "s"}],
            [{"r0l3": "P"}],
        ]
    )
    def test_post_incorrect_role(self, payload: dict) -> None:
        """Test HTTP_400 if request has wrong defined role"""
        response = self.client.post(self.url, json.dumps(payload), **self.headers)

        assert response.status_code == 400

    @parameterized.expand(
        [
            [
                {
                    "role": "P",
                    "height": 180,
                    "weight": 75,
                    "practice_distance": 20,
                    "prefered_leg": 1,
                },
            ],
            [
                {
                    "role": "P",
                    "team_object_id": 1,
                    "team_history_object_id": 1,
                }
            ],
            [
                {
                    "role": "T",
                    "licence": 1,
                    "team_object_id": 1,
                    "soccer_goal": 2,
                }
            ],
            [
                {
                    "role": "C",
                    "club_object_id": 1,
                    "club_role": CLUB_ROLE_TEAM_LEADER,
                    "phone": "111222333",
                }
            ],
            [{"role": "S", "soccer_goal": 2, "bio": "jakiesbio"}],
        ]
    )
    def test_successfully_create_profile_for_new_user(self, payload: dict) -> None:
        """Test creating profiles with correctly passed payload"""
        self.manager.login(self.user_obj)
        response = self.client.post(self.url, json.dumps(payload), **self.headers)

        assert response.status_code == 201
        assert response.data["user_id"] and response.data["role"]

        profile_type = utils.get_profile_by_role(payload["role"])
        profile = profile_type.objects.get(user=self.user_obj)

        for attr, val in payload.items():
            if attr != "role":
                assert getattr(profile, attr) == val

    @parameterized.expand([[{"user_id": 1, "role": "P"}]])
    def test_create_same_profile_type_twice_for_same_user(self, payload: dict) -> None:
        """
        Test HTTP_400 in attempt to create profile
        for user that has already a profile
        """
        self.client.post(self.url, json.dumps(payload), **self.headers)
        response = self.client.post(self.url, json.dumps(payload), **self.headers)

        assert response.status_code == 400

    # @parameterized.expand( # TODO(bartnyk) NOT READY, USER CAN HAVE JUST ONE PROFILE YET   # noqa: E501
    #     [
    #         [{"user_id": 1, "role": "P"}],
    #         [{"user_id": 1, "role": "S"}],
    #         [{"user_id": 1, "role": "C"}],
    #     ]
    # )
    # def test_create_multiple_profile_types_for_same_user(self, payload: dict) -> None:
    #     """
    #     Test HTTP_400 in attempt to create profile
    #     for user that has already a profile
    #     """
    #     response = ProfileAPI.as_view(
    #     {"post": "create_profile"})(get_request(payload)
    #     )
    #
    #     user = get_user(payload["user_id"])
    #     profile = get_profile_by_role(payload["role"])
    #     assert profile.objects.get(user=user)
    #     assert response.status_code == 201

    @parameterized.expand(
        [
            [
                {
                    "role": "P",
                },
                {
                    "height": 180,
                    "weight": 75,
                    "practice_distance": 20,
                    "prefered_leg": 1,
                },
            ],
            [
                {
                    "role": "P",
                },
                {
                    "team_object_id": 1,
                    "team_history_object_id": 1,
                },
            ],
            [
                {
                    "role": "T",
                },
                {
                    "licence": 1,
                    "team_object_id": 1,
                    "soccer_goal": 2,
                },
            ],
            [
                {
                    "role": "C",
                },
                {
                    "club_object_id": 1,
                    "club_role": "Kierownik",
                    "phone": "111222333",
                },
            ],
            [
                {
                    "role": "S",
                },
                {
                    "soccer_goal": 2,
                    "bio": "jakiesbio",
                },
            ],
        ]
    )
    def test_successfully_patch_profile_for_new_user(
        self, init_profile: dict, payload: dict
    ) -> None:
        """Test creating profiles with correctly passed payload"""
        profile = utils.create_empty_profile(**init_profile, user_id=self.user_obj.pk)
        profile_uuid = profile.uuid
        payload["uuid"] = str(profile_uuid)
        response = self.client.patch(self.url, json.dumps(payload), **self.headers)
        profile = utils.profile_service.get_profile_by_uuid(profile_uuid)

        assert response.status_code == 200
        for attr, val in payload.items():
            if attr == "uuid":
                val = uuid.UUID(val)
            assert getattr(profile, attr) == val

    def test_patch_fake_uuid(self) -> None:
        """patch request with fake uuid shouldn't pass"""
        fake_uuid = uuid.uuid4()
        self.manager.login(self.user_obj)
        response = self.client.patch(
            self.url, json.dumps({"uuid": str(fake_uuid)}), **self.headers
        )

        assert response.status_code == 404

    def test_patch_invalid_uuid(self) -> None:
        """patch request with invalid uuid shouldn't pass"""
        response = self.client.patch(
            self.url, json.dumps({"uuid": "invalid-uuid-1234"}), **self.headers
        )

        assert response.status_code == 400

    def test_post_need_authentication(self) -> None:
        """post request should require authentication"""
        response = self.client.post(
            self.url,
            json.dumps({"user_id": 1, "role": "S"}),
            format="json",
        )

        assert response.status_code == 401

    def test_patch_need_authentication(self) -> None:
        """patch request should require authentication"""
        profile = utils.create_empty_profile(
            **{
                "user_id": self.user_obj.pk,
                "role": "S",
            }
        )
        profile_uuid = str(profile.uuid)
        response = self.client.patch(
            self.url,
            json.dumps({"uuid": profile_uuid}),
            format="json",
        )

        assert response.status_code == 401

    def test_post_request_need_body(self) -> None:
        """post require request's body, fail if empty"""
        response = self.client.post(self.url, {}, **self.headers)

        assert response.status_code == 400

    def test_patch_request_need_body(self) -> None:
        """patch require request's body, fail if empty"""
        response = self.client.patch(self.url, {}, **self.headers)

        assert response.status_code == 400

    def test_patch_user_is_not_an_owner_of_profile(self) -> None:
        """request should return 400 if requestor is not an owner of updated profile"""
        dummy_user = factories.UserFactory.create()
        profile = utils.create_empty_profile(
            **{
                "user_id": dummy_user.pk,
                "role": "P",
            }
        )
        profile_uuid = str(profile.uuid)
        response = self.client.patch(self.url, {"uuid": profile_uuid}, **self.headers)

        assert response.status_code == 400
